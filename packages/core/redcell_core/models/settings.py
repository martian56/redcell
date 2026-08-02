from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class AppSettings(Base):
    __tablename__ = "app_settings"
    id: Mapped[str] = mapped_column(String, primary_key=True, default="global")
    llm: Mapped[dict] = mapped_column(JSONB, default=dict)
    execution: Mapped[dict] = mapped_column(JSONB, default=dict)
    scope: Mapped[dict] = mapped_column(JSONB, default=dict)
    proxy: Mapped[dict] = mapped_column(JSONB, default=dict)
    report: Mapped[dict] = mapped_column(JSONB, default=dict)
