from typing import Optional
from uuid import UUID

from sqlmodel import Session

from app.models.search_log import SearchLog, SearchType


class SearchLogRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def record(
        self,
        search_type: SearchType,
        query_text: Optional[str],
        filters: dict,
        user_id: Optional[UUID] = None,
    ) -> SearchLog:
        log = SearchLog(
            user_id=user_id,
            query_text=query_text,
            search_type=search_type,
            filters_json=filters,
        )
        self._s.add(log)
        self._s.commit()
        return log
