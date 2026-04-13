"""OpenStreetMap → Place import pipeline.

Shared between ``scripts/import_osm.py`` (CLI) and the
``POST /places/import-osm`` endpoint. Resolves a city via Nominatim,
queries Overpass for POIs, maps OSM tags to our ``Place`` model, and
runs each through ``IngestionService`` so embeddings + Qdrant upserts
happen in one pass — same pipeline as the seed endpoint.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.models.place import BudgetLevel, IndoorOutdoor, Place
from app.services.ingestion_service import IngestionService

logger = logging.getLogger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "findfieldai-osm-importer/0.1"

# OSM (key, value) -> (our category, budget, indoor_outdoor).
# Order matters: first match wins when an element has multiple mapped tags.
OSM_MAPPING: list[tuple[tuple[str, str], tuple[str, BudgetLevel, IndoorOutdoor]]] = [
    (("tourism", "viewpoint"), ("viewpoint", BudgetLevel.free, IndoorOutdoor.outdoor)),
    (("tourism", "museum"), ("museum", BudgetLevel.mid, IndoorOutdoor.indoor)),
    (("tourism", "gallery"), ("gallery", BudgetLevel.mid, IndoorOutdoor.indoor)),
    (("tourism", "attraction"), ("attraction", BudgetLevel.mid, IndoorOutdoor.both)),
    (("tourism", "artwork"), ("artwork", BudgetLevel.free, IndoorOutdoor.outdoor)),
    (("leisure", "park"), ("park", BudgetLevel.free, IndoorOutdoor.outdoor)),
    (("leisure", "garden"), ("garden", BudgetLevel.free, IndoorOutdoor.outdoor)),
    (("leisure", "playground"), ("playground", BudgetLevel.free, IndoorOutdoor.outdoor)),
    (("leisure", "nature_reserve"), ("nature_reserve", BudgetLevel.free, IndoorOutdoor.outdoor)),
    (("natural", "peak"), ("peak", BudgetLevel.free, IndoorOutdoor.outdoor)),
    (("natural", "beach"), ("beach", BudgetLevel.free, IndoorOutdoor.outdoor)),
    (("historic", "castle"), ("castle", BudgetLevel.mid, IndoorOutdoor.both)),
    (("historic", "ruins"), ("ruins", BudgetLevel.free, IndoorOutdoor.outdoor)),
    (("historic", "monument"), ("monument", BudgetLevel.free, IndoorOutdoor.outdoor)),
    (("amenity", "cafe"), ("cafe", BudgetLevel.low, IndoorOutdoor.indoor)),
    (("amenity", "restaurant"), ("restaurant", BudgetLevel.mid, IndoorOutdoor.indoor)),
    (("amenity", "bar"), ("bar", BudgetLevel.mid, IndoorOutdoor.indoor)),
    (("amenity", "pub"), ("pub", BudgetLevel.mid, IndoorOutdoor.indoor)),
]


class OSMImportError(RuntimeError):
    """Raised when OSM/Nominatim/Overpass fail to produce usable data."""


async def resolve_city_relation(
    client: httpx.AsyncClient, city: str, country: str
) -> int:
    """Return the OSM relation id for a city (for Overpass area queries)."""
    params = {"q": f"{city}, {country}", "format": "json", "limit": 5}
    r = await client.get(
        NOMINATIM_URL, params=params, headers={"User-Agent": USER_AGENT}
    )
    r.raise_for_status()
    for item in r.json():
        if item.get("osm_type") == "relation":
            return int(item["osm_id"])
    raise OSMImportError(
        f"Nominatim could not resolve a relation for: {city}, {country}"
    )


def build_overpass_query(area_relation_id: int) -> str:
    # Overpass area id = relation id + 3_600_000_000.
    area = area_relation_id + 3_600_000_000
    filters = "\n  ".join(
        f'nwr["{k}"="{v}"](area.a);' for (k, v), _ in OSM_MAPPING
    )
    return (
        "[out:json][timeout:90];\n"
        f"area({area})->.a;\n"
        "(\n"
        f"  {filters}\n"
        ");\n"
        "out center tags;\n"
    )


def _coords(el: dict[str, Any]) -> tuple[float | None, float | None]:
    if el.get("type") == "node":
        return el.get("lat"), el.get("lon")
    center = el.get("center") or {}
    return center.get("lat"), center.get("lon")


def element_to_place(
    el: dict[str, Any], city: str, country: str
) -> Place | None:
    tags = el.get("tags") or {}
    name = tags.get("name:en") or tags.get("name")
    if not name:
        return None

    category: str | None = None
    budget = BudgetLevel.mid
    io = IndoorOutdoor.outdoor
    for (k, v), (cat, b, i) in OSM_MAPPING:
        if tags.get(k) == v:
            category, budget, io = cat, b, i
            break
    if category is None:
        return None

    lat, lon = _coords(el)

    short = (
        tags.get("description:en")
        or tags.get("description")
        or f"{category.replace('_', ' ').title()} in {city}"
    )
    long_parts = [short]
    for label, key in (
        ("Cuisine", "cuisine"),
        ("Hours", "opening_hours"),
        ("Website", "website"),
    ):
        if tags.get(key):
            long_parts.append(f"{label}: {tags[key]}")

    extra_tags: list[str] = []
    if budget == BudgetLevel.free:
        extra_tags.append("free")
    if tags.get("outdoor_seating") == "yes":
        extra_tags.append("outdoor_seating")
    if tags.get("wheelchair") == "yes":
        extra_tags.append("wheelchair_accessible")
    if tags.get("internet_access") in ("wlan", "yes"):
        extra_tags.append("wifi")
    if tags.get("cuisine"):
        extra_tags.append(str(tags["cuisine"]).split(";", 1)[0])

    osm_type = el.get("type", "node")
    source_url = tags.get("website") or (
        f"https://www.openstreetmap.org/{osm_type}/{el.get('id')}"
    )

    return Place(
        title=name,
        short_description=short,
        long_description=". ".join(long_parts),
        country=country,
        city=city,
        latitude=lat,
        longitude=lon,
        category=category,
        tags=extra_tags,
        budget_level=budget,
        indoor_outdoor=io,
        source_url=source_url,
    )


async def fetch_osm_elements(city: str, country: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(timeout=120.0) as client:
        logger.info("Resolving '%s, %s' via Nominatim…", city, country)
        area_id = await resolve_city_relation(client, city, country)
        logger.info("Got OSM relation id=%s", area_id)

        query = build_overpass_query(area_id)
        logger.info("Querying Overpass (%d tag filters)…", len(OSM_MAPPING))
        r = await client.post(
            OVERPASS_URL,
            data={"data": query},
            headers={"User-Agent": USER_AGENT},
        )
        r.raise_for_status()
        return r.json().get("elements", [])


async def import_city_from_osm(
    ingestion: IngestionService,
    city: str,
    country: str,
    limit: int = 80,
) -> list[Place]:
    """Fetch POIs for a city from OSM and ingest them. Returns created places."""
    elements = await fetch_osm_elements(city, country)
    logger.info("Overpass returned %d raw elements", len(elements))

    await ingestion.ensure_collection()

    seen: set[str] = set()
    created: list[Place] = []
    for el in elements:
        if len(created) >= limit:
            break
        place = element_to_place(el, city, country)
        if place is None:
            continue
        key = place.title.strip().lower()
        if key in seen:
            continue
        seen.add(key)
        await ingestion.ingest_place(place)
        created.append(place)
    return created
