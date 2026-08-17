from sqlalchemy import BigInteger, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Run(Base):
    __tablename__ = "runs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    instruction: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, default="queued")
    phase: Mapped[str] = mapped_column(String, default="Reconnaissance")
    provider: Mapped[str | None] = mapped_column(String, nullable=True)
    started_at: Mapped[str] = mapped_column(String)
    elapsed_sec: Mapped[int] = mapped_column(Integer, default=0)
    tokens: Mapped[int] = mapped_column(BigInteger, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    model: Mapped[str] = mapped_column(String)
    budget_tokens: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
