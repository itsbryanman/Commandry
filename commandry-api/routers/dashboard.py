"""Dashboard router — aggregate stats and alerts."""

from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from database import get_db
from models import Agent, BudgetAlert, MCPServer, TokenUsage

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/stats")
def dashboard_stats(db: Session = Depends(get_db)):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    agents_running = db.execute(
        select(func.count()).select_from(Agent).where(Agent.status == "running")
    )
    agents_total = db.execute(select(func.count()).select_from(Agent))
    agents_blocked = db.execute(
        select(func.count()).select_from(Agent).where(Agent.status == "budget_blocked")
    )
    mcp_total = db.execute(select(func.count()).select_from(MCPServer))
    today_cost = db.execute(
        select(func.coalesce(func.sum(TokenUsage.cost_usd), 0)).where(TokenUsage.timestamp >= today_start)
    )
    active_alerts = db.execute(
        select(func.count()).select_from(BudgetAlert).where(BudgetAlert.acknowledged == False)
    )

    return {
        "agents_running": agents_running.scalar() or 0,
        "agents_total": agents_total.scalar() or 0,
        "agents_blocked": agents_blocked.scalar() or 0,
        "mcp_servers": mcp_total.scalar() or 0,
        "today_cost_usd": round(float(today_cost.scalar()), 4),
        "active_alerts": active_alerts.scalar() or 0,
    }


@router.get("/alerts")
def dashboard_alerts(db: Session = Depends(get_db)):
    result = db.execute(
        select(BudgetAlert)
        .order_by(BudgetAlert.triggered_at.desc())
        .limit(25)
    )
    return [
        {
            "id": a.id,
            "agent_id": a.agent_id,
            "alert_type": a.alert_type,
            "budget_type": a.budget_type,
            "period_key": a.period_key,
            "limit_usd": a.limit_usd,
            "actual_usd": a.actual_usd,
            "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
            "acknowledged": a.acknowledged,
        }
        for a in result.scalars().all()
    ]
