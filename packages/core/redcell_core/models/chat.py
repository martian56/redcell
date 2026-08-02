from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, index=True)
    role: Mapped[str] = mapped_column(String)
    text: Mapped[str] = mapped_column(Text, default="")
    options: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    ts: Mapped[str] = mapped_column(String)
