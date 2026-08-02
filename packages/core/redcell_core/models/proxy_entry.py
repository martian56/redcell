from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class ProxyEntry(Base):
    __tablename__ = "proxy_entries"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    method: Mapped[str] = mapped_column(String)
    url: Mapped[str] = mapped_column(String)
    status: Mapped[int] = mapped_column(Integer, default=0)
    length: Mapped[str] = mapped_column(String, default="")
    ts: Mapped[str] = mapped_column(String, index=True)
