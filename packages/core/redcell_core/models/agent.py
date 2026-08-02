from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class Agent(Base):
    __tablename__ = "agents"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="running")
    parent_id: Mapped[str | None] = mapped_column(String, nullable=True)
    action: Mapped[str] = mapped_column(Text, default="")
    calls: Mapped[int] = mapped_column(Integer, default=0)


class AgentEdge(Base):
    __tablename__ = "agent_edges"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    run_id: Mapped[str] = mapped_column(String, index=True)
    from_id: Mapped[str] = mapped_column(String)
    to_id: Mapped[str] = mapped_column(String)
