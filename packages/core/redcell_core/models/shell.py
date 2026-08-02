from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Shell(Base):
    __tablename__ = "shells"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    kind: Mapped[str] = mapped_column(String)
    label: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="idle")
    host: Mapped[str | None] = mapped_column(String, nullable=True)
    remote_addr: Mapped[str | None] = mapped_column(String, nullable=True)
    pty: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[str] = mapped_column(String)
