from sqlalchemy import String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class IntelEntity(Base):
    __tablename__ = "intel_entities"
    __table_args__ = (UniqueConstraint("session_id", "type", "value", name="uq_intel_entity"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    type: Mapped[str] = mapped_column(String)
    value: Mapped[str] = mapped_column(Text)
    label: Mapped[str] = mapped_column(String, default="")
    source: Mapped[str] = mapped_column(String, default="")
    meta: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[str] = mapped_column(String)


class IntelRelation(Base):
    __tablename__ = "intel_relations"
    __table_args__ = (UniqueConstraint("from_id", "to_id", "label", name="uq_intel_relation"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    from_id: Mapped[str] = mapped_column(String)
    to_id: Mapped[str] = mapped_column(String)
    label: Mapped[str] = mapped_column(String, default="related")
    created_at: Mapped[str] = mapped_column(String)
