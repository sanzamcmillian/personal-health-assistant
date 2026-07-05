from sqlalchemy import ForeignKey, Text, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base_model import BaseModel


class ChatSession(BaseModel):

    __tablename__ = "chat_sessions"

    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    messages = relationship(
        "Message",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class Message(BaseModel):

    __tablename__ = "messages"

    session_id = mapped_column(
        ForeignKey("chat_sessions.id")
    )

    role: Mapped[str] = mapped_column(
        String(20)
    )

    content: Mapped[str] = mapped_column(Text)

    session = relationship(
        "ChatSession",
        back_populates="messages",
    )