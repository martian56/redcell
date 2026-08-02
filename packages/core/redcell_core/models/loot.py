from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Loot(Base):
    __tablename__ = "loot"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    kind: Mapped[str] = mapped_column(String)
    label: Mapped[str] = mapped_column(String)
    value: Mapped[str] = mapped_column(Text, default="")
    source: Mapped[str] = mapped_column(String, default="")
    ts: Mapped[str] = mapped_column(String)
    file_id: Mapped[str | None] = mapped_column(String, nullable=True)
