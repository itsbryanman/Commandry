"""Agents router — CRUD + lifecycle."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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


def _agent_dict(a: Agent) -> dict:
    return {
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


@router.get("")
async def list_agents(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Agent).order_by(Agent.created_at.desc()))
    return [_agent_dict(a) for a in result.scalars().all()]


@router.post("", status_code=201)
async def create_agent(body: AgentCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.get(Agent, body.id)
    if existing:
        raise HTTPException(status_code=409, detail="Agent already exists")
    agent = Agent(**body.model_dump())
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return _agent_dict(agent)


@router.get("/{agent_id}")
async def get_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return _agent_dict(agent)


@router.put("/{agent_id}")
async def update_agent(agent_id: str, body: AgentUpdate, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(agent, k, v)
    agent.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(agent)
    return _agent_dict(agent)


@router.delete("/{agent_id}")
async def delete_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await db.delete(agent)
    await db.commit()
    return {"ok": True}


@router.post("/{agent_id}/start")
async def start_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.status = "running"
    agent.updated_at = datetime.utcnow()
    await db.commit()
    return {"ok": True, "status": "running"}


@router.post("/{agent_id}/stop")
async def stop_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.status = "stopped"
    agent.runtime_pid = None
    agent.updated_at = datetime.utcnow()
    await db.commit()
    return {"ok": True, "status": "stopped"}


@router.post("/{agent_id}/restart")
async def restart_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    agent = await db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.status = "running"
    agent.updated_at = datetime.utcnow()
    await db.commit()
    return {"ok": True, "status": "running"}
