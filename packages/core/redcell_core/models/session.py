from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Session(Base):
    __tablename__ = "sessions"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    client: Mapped[str] = mapped_column(String, default="")
    # "network" (web/host pentest) or "code" (source-code security scan).
    kind: Mapped[str] = mapped_column(String, default="network")
    # For a code scan: a public git repo URL or a local folder path to review.
    source: Mapped[str | None] = mapped_column(Text, nullable=True)
    scope: Mapped[list] = mapped_column(JSONB, default=list)
    targets: Mapped[list] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String, default="active")
    roe: Mapped[str | None] = mapped_column(Text, nullable=True)
    brief: Mapped[str | None] = mapped_column(Text, nullable=True)
    active_run_id: Mapped[str | None] = mapped_column(String, nullable=True)
    # Where runs execute (a saved Server) and how they egress (a saved Proxy).
    # Null server_id => local execution; null proxy_id => direct (no proxy).
    server_id: Mapped[str | None] = mapped_column(String, nullable=True)
    proxy_id: Mapped[str | None] = mapped_column(String, nullable=True)
    # Default model/provider for runs created in this session.
    provider: Mapped[str | None] = mapped_column(String, nullable=True)
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[str] = mapped_column(String)
