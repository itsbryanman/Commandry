"""Agents router — CRUD + lifecycle."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from budget_service import check_agent_budget_blocked, get_agent_budget_status
from database import get_db
from models import Agent

router = APIRouter(prefix="/api/agents", tags=["agents"])


class AgentCreate(BaseModel):
    id: str
    display_name: str
    owner: str = "admin"
    runtime_type: str = "custom"
    model_provider: str = "anthropic"
    model_id: str = "claude-sonnet-4-20250514"
    model_temperature: float = 0.3
    model_max_tokens: int = 8192
    system_prompt: Optional[str] = None
    budget_daily_usd: Optional[float] = None
    budget_monthly_usd: Optional[float] = None


class AgentUpdate(BaseModel):
    display_name: Optional[str] = None
    status: Optional[str] = None
    model_provider: Optional[str] = None
    model_id: Optional[str] = None
    model_temperature: Optional[float] = None
    model_max_tokens: Optional[int] = None
    system_prompt: Optional[str] = None
    budget_daily_usd: Optional[float] = None
    budget_monthly_usd: Optional[float] = None
    budget_alert_pct: Optional[float] = None
    budget_auto_kill: Optional[bool] = None


def _agent_dict(a: Agent, budget_status: dict | None = None) -> dict:
    d = {
        "id": a.id,
        "display_name": a.display_name,
        "owner": a.owner,
        "status": a.status,
        "runtime_type": a.runtime_type,
        "model_provider": a.model_provider,
        "model_id": a.model_id,
        "model_temperature": a.model_temperature,
        "model_max_tokens": a.model_max_tokens,
        "system_prompt": a.system_prompt,
        "budget_daily_usd": a.budget_daily_usd,
        "budget_monthly_usd": a.budget_monthly_usd,
        "budget_alert_pct": a.budget_alert_pct,
        "budget_auto_kill": a.budget_auto_kill,
        "system_prompt_version": a.system_prompt_version,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    }
    if budget_status is not None:
        d["budget_status"] = budget_status
    return d


@router.get("")
def list_agents(db: Session = Depends(get_db)):
    result = db.execute(select(Agent).order_by(Agent.created_at.desc()))
    return [_agent_dict(a) for a in result.scalars().all()]


@router.post("", status_code=201)
def create_agent(body: AgentCreate, db: Session = Depends(get_db)):
    existing = db.get(Agent, body.id)
    if existing:
        raise HTTPException(status_code=409, detail="Agent already exists")
    agent = Agent(**body.model_dump())
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return _agent_dict(agent)


@router.get("/{agent_id}")
def get_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    budget = get_agent_budget_status(db, agent_id)
    return _agent_dict(agent, budget_status=budget)


@router.put("/{agent_id}")
def update_agent(agent_id: str, body: AgentUpdate, db: Session = Depends(get_db)):
    agent = db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(agent, k, v)
    agent.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(agent)
    return _agent_dict(agent)


@router.delete("/{agent_id}")
def delete_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    db.delete(agent)
    db.commit()
    return {"ok": True}


@router.post("/{agent_id}/start")
def start_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # If agent is budget-blocked, re-evaluate in case the period rolled over
    if agent.status == "budget_blocked":
        still_blocked, reason = check_agent_budget_blocked(db, agent_id)
        if still_blocked:
            raise HTTPException(
                status_code=409,
                detail=f"Agent cannot start: {reason}",
            )
        # Period rolled over — agent was unblocked by check_agent_budget_blocked
        db.refresh(agent)

    agent.status = "running"
    agent.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "status": "running"}


@router.post("/{agent_id}/stop")
def stop_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.status = "stopped"
    agent.runtime_pid = None
    agent.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "status": "stopped"}


@router.post("/{agent_id}/restart")
def restart_agent(agent_id: str, db: Session = Depends(get_db)):
    agent = db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # If agent is budget-blocked, re-evaluate
    if agent.status == "budget_blocked":
        still_blocked, reason = check_agent_budget_blocked(db, agent_id)
        if still_blocked:
            raise HTTPException(
                status_code=409,
                detail=f"Agent cannot restart: {reason}",
            )
        db.refresh(agent)

    agent.status = "running"
    agent.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "status": "running"}
