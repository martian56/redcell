from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Server(Base):
    __tablename__ = "servers"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    host: Mapped[str] = mapped_column(String)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    ip: Mapped[str | None] = mapped_column(String, nullable=True)
    region: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="unchecked")
    cpu: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ram_gb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    running_sessions: Mapped[int] = mapped_column(Integer, default=0)
    secret_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Connection-test facts (populated by POST /servers/{id}/test).
    os: Mapped[str | None] = mapped_column(String, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_check: Mapped[str | None] = mapped_column(String, nullable=True)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[str] = mapped_column(String)
