from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class File(Base):
    __tablename__ = "files"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str | None] = mapped_column(String, nullable=True, index=True)
    bucket: Mapped[str] = mapped_column(String)
    object_key: Mapped[str] = mapped_column(String)
    filename: Mapped[str] = mapped_column(String)
    kind: Mapped[str] = mapped_column(String, default="upload")
    content_type: Mapped[str] = mapped_column(String, default="application/octet-stream")
    size: Mapped[int] = mapped_column(BigInteger, default=0)
    visibility: Mapped[str] = mapped_column(String, default="private")
    source: Mapped[str] = mapped_column(String, default="")
    created_at: Mapped[str] = mapped_column(String)
