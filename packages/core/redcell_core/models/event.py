from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Event(Base):
    """Durable activity-log entry for a run (mirrors what streams on events:{id})."""

    __tablename__ = "events"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[str] = mapped_column(String)
    type: Mapped[str] = mapped_column(String)
    text: Mapped[str] = mapped_column(Text, default="")
    ts: Mapped[str] = mapped_column(String)
