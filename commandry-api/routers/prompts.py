"""Prompts router — versioned system prompts."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import get_db
from models import Agent, PromptVersion

router = APIRouter(prefix="/api/prompts", tags=["prompts"])


class PromptSave(BaseModel):
    content: str
    tag: Optional[str] = None


@router.get("/{agent_id}")
def list_prompt_versions(agent_id: str, db: Session = Depends(get_db)):
    result = db.execute(
        select(PromptVersion)
        .where(PromptVersion.agent_id == agent_id)
        .order_by(PromptVersion.version.desc())
    )
    return [
        {
            "id": p.id,
            "version": p.version,
            "tag": p.tag,
            "content": p.content,
            "created_at": p.created_at.isoformat() if p.created_at else None,
            "created_by": p.created_by,
        }
        for p in result.scalars().all()
    ]


@router.post("/{agent_id}", status_code=201)
def save_prompt(agent_id: str, body: PromptSave, db: Session = Depends(get_db)):
    agent = db.get(Agent, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Determine next version
    max_ver = db.execute(
        select(func.coalesce(func.max(PromptVersion.version), 0)).where(PromptVersion.agent_id == agent_id)
    )
    next_ver = int(max_ver.scalar()) + 1

    pv = PromptVersion(agent_id=agent_id, version=next_ver, content=body.content, tag=body.tag)
    db.add(pv)

    # Also update agent's system_prompt
    agent.system_prompt = body.content
    agent.system_prompt_version = next_ver
    agent.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(pv)
    return {"id": pv.id, "version": next_ver}


@router.get("/{agent_id}/{version}")
def get_prompt_version(agent_id: str, version: int, db: Session = Depends(get_db)):
    result = db.execute(
        select(PromptVersion).where(PromptVersion.agent_id == agent_id, PromptVersion.version == version)
    )
    pv = result.scalar_one_or_none()
    if not pv:
        raise HTTPException(status_code=404, detail="Prompt version not found")
    return {
        "id": pv.id,
        "version": pv.version,
        "tag": pv.tag,
        "content": pv.content,
        "created_at": pv.created_at.isoformat() if pv.created_at else None,
    }
