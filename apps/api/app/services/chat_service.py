import json
import logging

from app.integrations.chat.base import ChatProvider
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.schemas.place import PlaceFilters
from app.schemas.search import PlaceSearchHit
from app.services.search_service import SearchService

logger = logging.getLogger(__name__)

_SYSTEM_GROUNDED = (
    "You are Findfield AI, a travel discovery assistant.\n"
    "You only discuss places that appear in RETRIEVED_PLACES below. "
    "Never invent places. If results are weak or empty, say so and ask ONE short "
    "clarifying question.\n\n"
    "Respond ONLY with a valid JSON object, no markdown fences:\n"
    '{"answer":"2-4 sentences why the top matches fit the request",'
    '"follow_up_question":"one short follow-up question or null",'
    '"concepts":["key","concepts","extracted","from","query"],'
    '"reasons":{"1":"why place 1 matches in 1 sentence","2":"..."}}'
)


class ChatService:
    def __init__(self, chat: ChatProvider, search: SearchService) -> None:
        self._chat = chat
        self._search = search

    async def query(self, req: ChatQueryRequest) -> ChatQueryResponse:
        search_result = await self._search.search_text(
            query=req.message,
            filters=PlaceFilters(),
            limit=5,
        )

        grounding = _format_grounding(search_result.hits)
        history = [{"role": m.role, "content": m.content} for m in req.history]
        messages = [
            {"role": "system", "content": _SYSTEM_GROUNDED},
            *history,
            {
                "role": "user",
                "content": (
                    f"RETRIEVED_PLACES:\n{grounding}\n\n"
                    f"USER_REQUEST: {req.message}"
                ),
            },
        ]
        raw = await self._chat.complete(messages=messages, max_tokens=600)

        try:
            data = json.loads(raw)
            answer = data.get("answer") or raw
            follow_up = data.get("follow_up_question") or None
            concepts = data.get("concepts") or []
            reasons: dict = data.get("reasons") or {}
        except (json.JSONDecodeError, ValueError):
            logger.warning("LLM did not return valid JSON, falling back to plain text")
            answer = raw
            follow_up = None
            concepts = []
            reasons = {}

        hits = [
            PlaceSearchHit(
                score=h.score,
                place=h.place,
                match_reason=reasons.get(str(i)),
            )
            for i, h in enumerate(search_result.hits, 1)
        ]

        return ChatQueryResponse(
            answer=answer,
            follow_up_question=follow_up,
            concepts=concepts,
            results=hits,
        )


def _format_grounding(hits) -> str:
    if not hits:
        return "(no places found — tell the user and ask a clarifying question)"
    lines = []
    for i, h in enumerate(hits, 1):
        p = h.place
        lines.append(
            f"{i}. {p.title} — {p.city}, {p.country} "
            f"[{p.category}, {p.budget_level}, {p.indoor_outdoor}] "
            f"score={h.score:.3f}\n   {p.short_description}"
        )
    return "\n".join(lines)
