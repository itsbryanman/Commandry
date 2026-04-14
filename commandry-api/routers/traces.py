"""Traces router — execution traces."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import ExecutionTrace

router = APIRouter(prefix="/api/traces", tags=["traces"])


class TraceCreate(BaseModel):
    id: str
    agent_id: str
    triggered_by: str = "manual"
    status: str = "running"


class TraceUpdate(BaseModel):
    status: Optional[str] = None
    ended_at: Optional[str] = None
    turns: Optional[int] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    cost_usd: Optional[float] = None
    tools_called: Optional[str] = None
    errors: Optional[str] = None


def _trace_dict(t: ExecutionTrace) -> dict:
    return {
        "id": t.id,
        "agent_id": t.agent_id,
        "triggered_by": t.triggered_by,
        "started_at": t.started_at.isoformat() if t.started_at else None,
        "ended_at": t.ended_at.isoformat() if t.ended_at else None,
        "status": t.status,
        "turns": t.turns,
        "input_tokens": t.input_tokens,
        "output_tokens": t.output_tokens,
        "cost_usd": t.cost_usd,
        "tools_called": t.tools_called,
        "errors": t.errors,
    }


@router.get("")
async def list_traces(agent_id: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    q = select(ExecutionTrace).order_by(ExecutionTrace.started_at.desc()).limit(100)
    if agent_id:
        q = q.where(ExecutionTrace.agent_id == agent_id)
    result = await db.execute(q)
    return [_trace_dict(t) for t in result.scalars().all()]


@router.post("", status_code=201)
async def create_trace(body: TraceCreate, db: AsyncSession = Depends(get_db)):
    trace = ExecutionTrace(**body.model_dump())
    db.add(trace)
    await db.commit()
    await db.refresh(trace)
    return _trace_dict(trace)


@router.get("/{trace_id}")
async def get_trace(trace_id: str, db: AsyncSession = Depends(get_db)):
    trace = await db.get(ExecutionTrace, trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return _trace_dict(trace)


@router.put("/{trace_id}")
async def update_trace(trace_id: str, body: TraceUpdate, db: AsyncSession = Depends(get_db)):
    trace = await db.get(ExecutionTrace, trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        if k == "ended_at" and v:
            setattr(trace, k, datetime.fromisoformat(v))
        else:
            setattr(trace, k, v)
    await db.commit()
    await db.refresh(trace)
    return _trace_dict(trace)
