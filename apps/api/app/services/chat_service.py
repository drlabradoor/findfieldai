import logging

from app.integrations.chat.base import ChatProvider
from app.schemas.chat import ChatQueryRequest, ChatQueryResponse
from app.schemas.place import PlaceFilters
from app.services.search_service import SearchService

logger = logging.getLogger(__name__)

_SYSTEM_GROUNDED = (
    "You are Findfield AI, a travel discovery assistant.\n"
    "You only discuss places that appear in RETRIEVED_PLACES below. "
    "Never invent places. If results are weak or empty, say so and ask ONE short "
    "clarifying question. Keep answers short (2-4 sentences) and explain why "
    "the top matches fit the user request."
)


class ChatService:
    """Grounded chat orchestration.

    Two-step: run retrieval first, then call the LLM with the retrieved
    places as the only source of truth. LLM is a formatter, not the search
    engine.
    """

    def __init__(self, chat: ChatProvider, search: SearchService) -> None:
        self._chat = chat
        self._search = search

    async def query(self, req: ChatQueryRequest) -> ChatQueryResponse:
        # MVP: no intent extraction yet — pass the raw message as the query.
        # TODO: add an extract step that returns PlaceFilters from free text.
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
        answer = await self._chat.complete(messages=messages, max_tokens=400)
        return ChatQueryResponse(
            answer=answer,
            results=search_result.hits,
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
