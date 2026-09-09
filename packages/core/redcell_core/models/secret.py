from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Secret(Base):
    __tablename__ = "secrets"
    name: Mapped[str] = mapped_column(String, primary_key=True)
    value_enc: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String)
