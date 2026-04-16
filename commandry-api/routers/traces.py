"""Traces router — execution traces."""

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from budget_service import check_agent_budget_blocked
from database import get_db
from models import Agent, ExecutionTrace

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
def list_traces(agent_id: Optional[str] = None, status: Optional[str] = None, db: Session = Depends(get_db)):
    q = select(ExecutionTrace).order_by(ExecutionTrace.started_at.desc()).limit(100)
    if agent_id:
        q = q.where(ExecutionTrace.agent_id == agent_id)
    if status:
        q = q.where(ExecutionTrace.status == status)
    result = db.execute(q)
    return [_trace_dict(t) for t in result.scalars().all()]


@router.post("", status_code=201)
def create_trace(body: TraceCreate, db: Session = Depends(get_db)):
    # Check if agent is budget-blocked before allowing a new execution
    agent = db.get(Agent, body.agent_id)
    if agent and agent.status == "budget_blocked":
        still_blocked, reason = check_agent_budget_blocked(db, body.agent_id)
        if still_blocked:
            # Record a budget_blocked trace for auditability
            trace = ExecutionTrace(
                id=body.id,
                agent_id=body.agent_id,
                triggered_by=body.triggered_by,
                status="budget_blocked",
                started_at=datetime.utcnow(),
                ended_at=datetime.utcnow(),
                turns=0,
                input_tokens=0,
                output_tokens=0,
                cost_usd=0.0,
                errors=json.dumps([{"code": "BUDGET_EXCEEDED", "message": reason}]),
            )
            db.add(trace)
            db.commit()
            db.refresh(trace)
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "BUDGET_EXCEEDED",
                    "message": f"Agent '{body.agent_id}' is blocked: {reason}",
                    "trace_id": trace.id,
                },
            )

    trace = ExecutionTrace(**body.model_dump())
    db.add(trace)
    db.commit()
    db.refresh(trace)
    return _trace_dict(trace)


@router.get("/{trace_id}")
def get_trace(trace_id: str, db: Session = Depends(get_db)):
    trace = db.get(ExecutionTrace, trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    return _trace_dict(trace)


@router.put("/{trace_id}")
def update_trace(trace_id: str, body: TraceUpdate, db: Session = Depends(get_db)):
    trace = db.get(ExecutionTrace, trace_id)
    if not trace:
        raise HTTPException(status_code=404, detail="Trace not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        if k == "ended_at" and v:
            setattr(trace, k, datetime.fromisoformat(v))
        else:
            setattr(trace, k, v)
    db.commit()
    db.refresh(trace)
    return _trace_dict(trace)
