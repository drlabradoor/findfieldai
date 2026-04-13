from uuid import UUID

from fastapi import APIRouter, Depends

from app.deps import get_favorite_repo, get_place_repo
from app.repositories.favorite_repo import FavoriteRepository
from app.repositories.place_repo import PlaceRepository
from app.schemas.favorite import FavoriteOut
from app.schemas.place import PlaceOut

router = APIRouter(prefix="/favorites", tags=["favorites"])


# MVP: user_id passed as header via ?user_id= query until Supabase Auth is wired in.
# TODO: replace with a proper get_current_user dependency.


@router.get("", response_model=list[FavoriteOut])
async def list_favorites(
    user_id: UUID,
    favs: FavoriteRepository = Depends(get_favorite_repo),
    places: PlaceRepository = Depends(get_place_repo),
) -> list[FavoriteOut]:
    favorites = favs.list_for_user(user_id)
    place_map = {p.id: p for p in places.get_many([f.place_id for f in favorites])}
    images_by_place = places.images_for(list(place_map.keys()))
    out: list[FavoriteOut] = []
    for fav in favorites:
        place = place_map.get(fav.place_id)
        if not place:
            continue
        out.append(
            FavoriteOut(
                id=fav.id,
                created_at=fav.created_at,
                place=PlaceOut.from_model(place, images_by_place.get(place.id, [])),
            )
        )
    return out


@router.post("/{place_id}")
async def add_favorite(
    place_id: UUID,
    user_id: UUID,
    favs: FavoriteRepository = Depends(get_favorite_repo),
) -> dict:
    fav = favs.add(user_id=user_id, place_id=place_id)
    return {"id": str(fav.id)}


@router.delete("/{place_id}")
async def remove_favorite(
    place_id: UUID,
    user_id: UUID,
    favs: FavoriteRepository = Depends(get_favorite_repo),
) -> dict:
    favs.remove(user_id=user_id, place_id=place_id)
    return {"ok": True}
