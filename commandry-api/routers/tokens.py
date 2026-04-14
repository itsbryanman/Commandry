"""Tokens & pricing router."""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import BudgetAlert, ProviderPricing, TokenUsage

router = APIRouter(tags=["tokens"])


# ── Token ingestion ──────────────────────────────────────────────
class TokenIngest(BaseModel):
    agent_id: Optional[str] = None
    provider: str
    model_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    trace_id: Optional[str] = None
    session_id: Optional[str] = None


@router.post("/api/tokens/ingest", status_code=201)
async def ingest_tokens(body: TokenIngest, db: AsyncSession = Depends(get_db)):
    # Look up pricing
    result = await db.execute(
        select(ProviderPricing)
        .where(ProviderPricing.provider == body.provider, ProviderPricing.model_id == body.model_id)
        .order_by(ProviderPricing.effective_date.desc())
        .limit(1)
    )
    pricing = result.scalar_one_or_none()
    cost = 0.0
    if pricing:
        cost += (body.input_tokens / 1_000_000) * pricing.input_price_per_mtok
        cost += (body.output_tokens / 1_000_000) * pricing.output_price_per_mtok
        cost += (body.cache_read_tokens / 1_000_000) * pricing.cache_read_price_per_mtok
        cost += (body.cache_write_tokens / 1_000_000) * pricing.cache_write_price_per_mtok

    usage = TokenUsage(
        agent_id=body.agent_id,
        provider=body.provider,
        model_id=body.model_id,
        input_tokens=body.input_tokens,
        output_tokens=body.output_tokens,
        cache_read_tokens=body.cache_read_tokens,
        cache_write_tokens=body.cache_write_tokens,
        cost_usd=cost,
        trace_id=body.trace_id,
        session_id=body.session_id,
    )
    db.add(usage)
    await db.commit()
    await db.refresh(usage)
    return {"id": usage.id, "cost_usd": cost}


@router.get("/api/tokens/summary")
async def token_summary(db: AsyncSession = Depends(get_db)):
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    today_q = await db.execute(
        select(func.coalesce(func.sum(TokenUsage.cost_usd), 0)).where(TokenUsage.timestamp >= today_start)
    )
    month_q = await db.execute(
        select(func.coalesce(func.sum(TokenUsage.cost_usd), 0)).where(TokenUsage.timestamp >= month_start)
    )
    total_q = await db.execute(select(func.coalesce(func.sum(TokenUsage.cost_usd), 0)))

    return {
        "today_usd": round(float(today_q.scalar()), 4),
        "month_usd": round(float(month_q.scalar()), 4),
        "total_usd": round(float(total_q.scalar()), 4),
    }


@router.get("/api/tokens/by-agent/{agent_id}")
async def tokens_by_agent(agent_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(TokenUsage).where(TokenUsage.agent_id == agent_id).order_by(TokenUsage.timestamp.desc()).limit(100)
    )
    rows = result.scalars().all()
    return [
        {
            "id": r.id,
            "timestamp": r.timestamp.isoformat() if r.timestamp else None,
            "model_id": r.model_id,
            "input_tokens": r.input_tokens,
            "output_tokens": r.output_tokens,
            "cost_usd": r.cost_usd,
        }
        for r in rows
    ]


@router.get("/api/tokens/by-model")
async def tokens_by_model(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            TokenUsage.model_id,
            func.sum(TokenUsage.input_tokens).label("total_input"),
            func.sum(TokenUsage.output_tokens).label("total_output"),
            func.sum(TokenUsage.cost_usd).label("total_cost"),
        ).group_by(TokenUsage.model_id)
    )
    return [
        {"model_id": row.model_id, "total_input": row.total_input, "total_output": row.total_output, "total_cost": round(float(row.total_cost), 4)}
        for row in result.all()
    ]


# ── Pricing CRUD ─────────────────────────────────────────────────
class PricingCreate(BaseModel):
    provider: str
    model_id: str
    input_price_per_mtok: float
    output_price_per_mtok: float
    cache_read_price_per_mtok: float = 0
    cache_write_price_per_mtok: float = 0
    effective_date: str


@router.get("/api/pricing")
async def list_pricing(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ProviderPricing).order_by(ProviderPricing.provider, ProviderPricing.model_id))
    return [
        {
            "id": p.id,
            "provider": p.provider,
            "model_id": p.model_id,
            "input_price_per_mtok": p.input_price_per_mtok,
            "output_price_per_mtok": p.output_price_per_mtok,
            "effective_date": p.effective_date,
        }
        for p in result.scalars().all()
    ]


@router.post("/api/pricing", status_code=201)
async def create_pricing(body: PricingCreate, db: AsyncSession = Depends(get_db)):
    p = ProviderPricing(**body.model_dump())
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return {"id": p.id}


@router.put("/api/pricing/{pricing_id}")
async def update_pricing(pricing_id: int, body: PricingCreate, db: AsyncSession = Depends(get_db)):
    p = await db.get(ProviderPricing, pricing_id)
    if not p:
        raise HTTPException(status_code=404, detail="Pricing not found")
    for k, v in body.model_dump().items():
        setattr(p, k, v)
    await db.commit()
    return {"ok": True}


# ── Budget alerts ────────────────────────────────────────────────
@router.get("/api/budget/alerts")
async def list_alerts(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BudgetAlert).order_by(BudgetAlert.triggered_at.desc()).limit(50))
    return [
        {
            "id": a.id,
            "agent_id": a.agent_id,
            "alert_type": a.alert_type,
            "budget_type": a.budget_type,
            "limit_usd": a.limit_usd,
            "actual_usd": a.actual_usd,
            "triggered_at": a.triggered_at.isoformat() if a.triggered_at else None,
            "acknowledged": a.acknowledged,
        }
        for a in result.scalars().all()
    ]


@router.post("/api/budget/alerts/{alert_id}/ack")
async def ack_alert(alert_id: int, db: AsyncSession = Depends(get_db)):
    a = await db.get(BudgetAlert, alert_id)
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")
    a.acknowledged = True
    await db.commit()
    return {"ok": True}
