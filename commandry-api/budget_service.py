"""Budget enforcement service.

Evaluates agent spending against configured daily/monthly budgets.
Creates alerts at threshold crossings and blocks agents on overspend.

Budget periods use UTC:
  - Daily: midnight-to-midnight UTC, period_key format "YYYY-MM-DD"
  - Monthly: first-of-month midnight UTC, period_key format "YYYY-MM"

Threshold levels:
  - warning:  spend >= agent.budget_alert_pct % of limit (default 80%)
  - critical: spend >= 95% of limit
  - exceeded: spend >= 100% of limit

Duplicate prevention:
  A unique constraint on (agent_id, alert_type, budget_type, period_key)
  ensures each alert fires at most once per agent per budget type per period.
  IntegrityError on insert is caught and treated as a no-op.
"""

from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models import Agent, BudgetAlert, TokenUsage


CRITICAL_PCT = 95.0


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _today_start_utc() -> datetime:
    now = _utc_now()
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def _month_start_utc() -> datetime:
    now = _utc_now()
    return now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def _daily_period_key() -> str:
    return _utc_now().strftime("%Y-%m-%d")


def _monthly_period_key() -> str:
    return _utc_now().strftime("%Y-%m")


def get_agent_daily_spend(db: Session, agent_id: str) -> float:
    """Sum of cost_usd for the agent in the current UTC day."""
    result = db.execute(
        select(func.coalesce(func.sum(TokenUsage.cost_usd), 0.0))
        .where(TokenUsage.agent_id == agent_id)
        .where(TokenUsage.timestamp >= _today_start_utc())
    )
    return float(result.scalar())


def get_agent_monthly_spend(db: Session, agent_id: str) -> float:
    """Sum of cost_usd for the agent in the current UTC month."""
    result = db.execute(
        select(func.coalesce(func.sum(TokenUsage.cost_usd), 0.0))
        .where(TokenUsage.agent_id == agent_id)
        .where(TokenUsage.timestamp >= _month_start_utc())
    )
    return float(result.scalar())


def _try_create_alert(
    db: Session,
    agent_id: str,
    alert_type: str,
    budget_type: str,
    period_key: str,
    limit_usd: float,
    actual_usd: float,
) -> bool:
    """Attempt to insert a budget alert. Returns True if created, False if duplicate."""
    alert = BudgetAlert(
        agent_id=agent_id,
        alert_type=alert_type,
        budget_type=budget_type,
        period_key=period_key,
        limit_usd=round(limit_usd, 4),
        actual_usd=round(actual_usd, 4),
        triggered_at=_utc_now(),
    )
    db.add(alert)
    try:
        db.flush()
        return True
    except IntegrityError:
        db.rollback()
        return False


def _check_thresholds(
    db: Session,
    agent: Agent,
    budget_type: str,
    limit_usd: float,
    actual_usd: float,
    period_key: str,
) -> bool:
    """Check spend against thresholds for one budget type. Returns True if exceeded."""
    if limit_usd <= 0:
        return False

    # Use Decimal for precise percentage comparison
    actual = Decimal(str(actual_usd))
    limit = Decimal(str(limit_usd))
    pct = (actual / limit * Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    warning_pct = Decimal(str(agent.budget_alert_pct or 80.0))
    critical_pct = Decimal(str(CRITICAL_PCT))
    exceeded_pct = Decimal("100.00")

    exceeded = False

    if pct >= warning_pct:
        _try_create_alert(db, agent.id, "warning", budget_type, period_key, limit_usd, actual_usd)

    if pct >= critical_pct:
        _try_create_alert(db, agent.id, "critical", budget_type, period_key, limit_usd, actual_usd)

    if pct >= exceeded_pct:
        _try_create_alert(db, agent.id, "exceeded", budget_type, period_key, limit_usd, actual_usd)
        exceeded = True

    return exceeded


def evaluate_budget(db: Session, agent_id: str) -> dict:
    """Evaluate budget for an agent after a cost ingest.

    Returns a dict with:
      - daily_spend, monthly_spend: current period totals
      - daily_exceeded, monthly_exceeded: whether each budget is blown
      - blocked: whether the agent was blocked by this evaluation
      - alerts_created: count of new alerts created in this call
    """
    agent = db.get(Agent, agent_id)
    if not agent:
        return {"blocked": False, "alerts_created": 0}

    daily_spend = get_agent_daily_spend(db, agent_id)
    monthly_spend = get_agent_monthly_spend(db, agent_id)

    daily_exceeded = False
    monthly_exceeded = False

    # Check daily budget
    if agent.budget_daily_usd and agent.budget_daily_usd > 0:
        daily_exceeded = _check_thresholds(
            db, agent, "daily", agent.budget_daily_usd, daily_spend, _daily_period_key()
        )

    # Check monthly budget
    if agent.budget_monthly_usd and agent.budget_monthly_usd > 0:
        monthly_exceeded = _check_thresholds(
            db, agent, "monthly", agent.budget_monthly_usd, monthly_spend, _monthly_period_key()
        )

    blocked = False
    if (daily_exceeded or monthly_exceeded) and agent.budget_auto_kill:
        if agent.status != "budget_blocked":
            agent.status = "budget_blocked"
            agent.updated_at = _utc_now()
            blocked = True

    db.commit()

    return {
        "daily_spend": round(daily_spend, 4),
        "monthly_spend": round(monthly_spend, 4),
        "daily_exceeded": daily_exceeded,
        "monthly_exceeded": monthly_exceeded,
        "blocked": blocked,
    }


def check_agent_budget_blocked(db: Session, agent_id: str) -> tuple[bool, str]:
    """Check if an agent is currently blocked by budget.

    Performs a live re-evaluation of current period spend, so that
    period rollover automatically unblocks agents.

    Returns (is_blocked, reason_message).
    """
    agent = db.get(Agent, agent_id)
    if not agent:
        return False, ""

    if agent.status != "budget_blocked":
        return False, ""

    # Re-evaluate: maybe the budget period rolled over
    daily_ok = True
    monthly_ok = True

    if agent.budget_daily_usd and agent.budget_daily_usd > 0:
        daily_spend = get_agent_daily_spend(db, agent_id)
        if daily_spend >= agent.budget_daily_usd:
            daily_ok = False

    if agent.budget_monthly_usd and agent.budget_monthly_usd > 0:
        monthly_spend = get_agent_monthly_spend(db, agent_id)
        if monthly_spend >= agent.budget_monthly_usd:
            monthly_ok = False

    if daily_ok and monthly_ok:
        # Period rolled over, spend is under budget now — unblock
        agent.status = "stopped"
        agent.updated_at = _utc_now()
        db.commit()
        return False, ""

    reasons = []
    if not daily_ok:
        reasons.append(
            f"daily budget exceeded (${daily_spend:.2f} / ${agent.budget_daily_usd:.2f})"
        )
    if not monthly_ok:
        reasons.append(
            f"monthly budget exceeded (${monthly_spend:.2f} / ${agent.budget_monthly_usd:.2f})"
        )

    return True, "; ".join(reasons)


def get_agent_budget_status(db: Session, agent_id: str) -> dict:
    """Return full budget status for an agent, suitable for API responses."""
    agent = db.get(Agent, agent_id)
    if not agent:
        return {}

    daily_spend = get_agent_daily_spend(db, agent_id)
    monthly_spend = get_agent_monthly_spend(db, agent_id)

    daily_pct = 0.0
    monthly_pct = 0.0
    daily_state = "ok"
    monthly_state = "ok"

    if agent.budget_daily_usd and agent.budget_daily_usd > 0:
        daily_pct = round((daily_spend / agent.budget_daily_usd) * 100, 1)
        warning = agent.budget_alert_pct or 80.0
        if daily_pct >= 100:
            daily_state = "exceeded"
        elif daily_pct >= CRITICAL_PCT:
            daily_state = "critical"
        elif daily_pct >= warning:
            daily_state = "warning"

    if agent.budget_monthly_usd and agent.budget_monthly_usd > 0:
        monthly_pct = round((monthly_spend / agent.budget_monthly_usd) * 100, 1)
        warning = agent.budget_alert_pct or 80.0
        if monthly_pct >= 100:
            monthly_state = "exceeded"
        elif monthly_pct >= CRITICAL_PCT:
            monthly_state = "critical"
        elif monthly_pct >= warning:
            monthly_state = "warning"

    is_blocked = agent.status == "budget_blocked"

    # Recent alerts for this agent (last 10)
    result = db.execute(
        select(BudgetAlert)
        .where(BudgetAlert.agent_id == agent_id)
        .order_by(BudgetAlert.triggered_at.desc())
        .limit(10)
    )
    recent_alerts = [
        {
            "id": a.id,
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

    return {
        "daily_spend_usd": round(daily_spend, 4),
        "monthly_spend_usd": round(monthly_spend, 4),
        "daily_budget_usd": agent.budget_daily_usd,
        "monthly_budget_usd": agent.budget_monthly_usd,
        "daily_pct": daily_pct,
        "monthly_pct": monthly_pct,
        "daily_state": daily_state,
        "monthly_state": monthly_state,
        "budget_alert_pct": agent.budget_alert_pct or 80.0,
        "budget_auto_kill": agent.budget_auto_kill,
        "is_blocked": is_blocked,
        "recent_alerts": recent_alerts,
    }
