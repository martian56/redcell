from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Agent, AgentEdge
from . import ids


async def graph(s: AsyncSession, run_id: str) -> tuple[list[Agent], list[AgentEdge]]:
    nodes = list((await s.scalars(select(Agent).where(Agent.run_id == run_id))).all())
    edges = list((await s.scalars(select(AgentEdge).where(AgentEdge.run_id == run_id))).all())
    return nodes, edges


async def get(s: AsyncSession, aid: str) -> Agent | None:
    return await s.get(Agent, aid)


async def add(s: AsyncSession, data: dict) -> Agent:
    row = Agent(id=data.get("id") or ids.new_id("ag"), **{k: v for k, v in data.items() if k != "id"})
    s.add(row)
    await s.flush()
    return row


async def update(s: AsyncSession, aid: str, **fields) -> None:
    row = await s.get(Agent, aid)
    if row:
        for k, v in fields.items():
            setattr(row, k, v)
        await s.flush()


async def add_edge(s: AsyncSession, run_id: str, from_id: str, to_id: str) -> AgentEdge:
    row = AgentEdge(id=ids.new_id("edge"), run_id=run_id, from_id=from_id, to_id=to_id)
    s.add(row)
    await s.flush()
    return row
