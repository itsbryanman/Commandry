"""Dashboard router — aggregate stats."""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import Agent, MCPServer, TokenUsage

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
async def dashboard_stats(db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    agents_running = await db.execute(
        select(func.count()).select_from(Agent).where(Agent.status == "running")
    )
    agents_total = await db.execute(select(func.count()).select_from(Agent))
    mcp_total = await db.execute(select(func.count()).select_from(MCPServer))
    today_cost = await db.execute(
        select(func.coalesce(func.sum(TokenUsage.cost_usd), 0)).where(TokenUsage.timestamp >= today_start)
    )

    return {
        "agents_running": agents_running.scalar() or 0,
        "agents_total": agents_total.scalar() or 0,
        "mcp_servers": mcp_total.scalar() or 0,
        "today_cost_usd": round(float(today_cost.scalar()), 4),
    }
