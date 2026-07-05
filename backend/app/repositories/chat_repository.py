from sqlalchemy.orm import Session

from app.models.chat import ChatSession
from app.repositories.base_repository import BaseRepository


class ChatRepository(
    BaseRepository[ChatSession]
):

    def __init__(self, db: Session):
        super().__init__(db)

    def list_sessions(self):
        return (
            self.db.query(ChatSession)
            .order_by(
                ChatSession.created_at.desc()
            )
            .all()
        )