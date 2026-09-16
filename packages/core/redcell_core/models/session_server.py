from sqlalchemy import String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class SessionServer(Base):
    __tablename__ = "session_servers"
    __table_args__ = (UniqueConstraint("session_id", "server_id", "role", name="uq_session_server_role"),)
    id: Mapped[str] = mapped_column(String, primary_key=True)
    session_id: Mapped[str] = mapped_column(String, index=True)
    server_id: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default="execution")
    created_at: Mapped[str] = mapped_column(String)
