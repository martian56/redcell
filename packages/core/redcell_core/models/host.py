from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Host(Base):
    __tablename__ = "hosts"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    host: Mapped[str] = mapped_column(String)
    ip: Mapped[str | None] = mapped_column(String, nullable=True)
    ports: Mapped[list] = mapped_column(JSONB, default=list)
    tech: Mapped[list] = mapped_column(JSONB, default=list)
    source: Mapped[str] = mapped_column(String, default="")
