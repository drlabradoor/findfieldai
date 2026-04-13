from uuid import UUID

from sqlmodel import Session, select

from app.models.favorite import Favorite


class FavoriteRepository:
    def __init__(self, session: Session) -> None:
        self._s = session

    def list_for_user(self, user_id: UUID) -> list[Favorite]:
        stmt = select(Favorite).where(Favorite.user_id == user_id)
        return list(self._s.exec(stmt).all())

    def add(self, user_id: UUID, place_id: UUID) -> Favorite:
        fav = Favorite(user_id=user_id, place_id=place_id)
        self._s.add(fav)
        self._s.commit()
        self._s.refresh(fav)
        return fav

    def remove(self, user_id: UUID, place_id: UUID) -> None:
        stmt = select(Favorite).where(
            Favorite.user_id == user_id,
            Favorite.place_id == place_id,
        )
        for fav in self._s.exec(stmt).all():
            self._s.delete(fav)
        self._s.commit()
