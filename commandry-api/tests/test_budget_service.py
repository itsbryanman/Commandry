"""Tests for budget_service — threshold evaluation, alert creation, enforcement."""

from datetime import datetime, timezone, timedelta
from unittest.mock import patch

import pytest
from sqlalchemy import select

from budget_service import (
    CRITICAL_PCT,
    evaluate_budget,
    check_agent_budget_blocked,
    get_agent_budget_status,
    get_agent_daily_spend,
    get_agent_monthly_spend,
)
from models import Agent, BudgetAlert, TokenUsage
from tests.conftest import make_agent


# ── Helpers ──────────────────────────────────────────────────────────

def _add_usage(db, agent_id, cost, timestamp=None):
    """Insert a TokenUsage row with the given cost."""
    ts = timestamp or datetime.now(timezone.utc)
    usage = TokenUsage(
        agent_id=agent_id,
        provider="anthropic",
        model_id="claude-sonnet-4-20250514",
        input_tokens=1000,
        output_tokens=500,
        cost_usd=cost,
        timestamp=ts,
    )
    db.add(usage)
    db.commit()
    return usage


def _count_alerts(db, agent_id, alert_type=None, budget_type=None):
    q = select(BudgetAlert).where(BudgetAlert.agent_id == agent_id)
    if alert_type:
        q = q.where(BudgetAlert.alert_type == alert_type)
    if budget_type:
        q = q.where(BudgetAlert.budget_type == budget_type)
    return len(db.execute(q).scalars().all())


# ── No Budget Configured ────────────────────────────────────────────

class TestNoBudget:
    def test_no_budget_no_alerts(self, db_session):
        """Agent with no budget configured should produce no alerts."""
        make_agent(db_session, budget_daily_usd=None, budget_monthly_usd=None)
        _add_usage(db_session, "test-agent", 100.0)
        result = evaluate_budget(db_session, "test-agent")
        assert result["blocked"] is False
        assert result["daily_exceeded"] is False
        assert result["monthly_exceeded"] is False
        assert _count_alerts(db_session, "test-agent") == 0

    def test_nonexistent_agent(self, db_session):
        """Evaluating budget for nonexistent agent is a no-op."""
        result = evaluate_budget(db_session, "ghost")
        assert result["blocked"] is False


# ── Daily Budget ────────────────────────────────────────────────────

class TestDailyBudget:
    def test_below_warning_no_alerts(self, db_session):
        """Spend below warning threshold creates no alerts."""
        make_agent(db_session, budget_daily_usd=10.0, budget_alert_pct=80.0)
        _add_usage(db_session, "test-agent", 7.0)  # 70%
        result = evaluate_budget(db_session, "test-agent")
        assert result["daily_exceeded"] is False
        assert _count_alerts(db_session, "test-agent") == 0

    def test_warning_threshold(self, db_session):
        """Crossing warning threshold creates a warning alert."""
        make_agent(db_session, budget_daily_usd=10.0, budget_alert_pct=80.0)
        _add_usage(db_session, "test-agent", 8.1)  # 81%
        evaluate_budget(db_session, "test-agent")
        assert _count_alerts(db_session, "test-agent", "warning", "daily") == 1
        assert _count_alerts(db_session, "test-agent", "critical", "daily") == 0

    def test_critical_threshold(self, db_session):
        """Crossing critical threshold (95%) creates warning + critical alerts."""
        make_agent(db_session, budget_daily_usd=10.0, budget_alert_pct=80.0)
        _add_usage(db_session, "test-agent", 9.6)  # 96%
        evaluate_budget(db_session, "test-agent")
        assert _count_alerts(db_session, "test-agent", "warning", "daily") == 1
        assert _count_alerts(db_session, "test-agent", "critical", "daily") == 1
        assert _count_alerts(db_session, "test-agent", "exceeded", "daily") == 0

    def test_exceeded_threshold_blocks_agent(self, db_session):
        """Crossing 100% creates all three alerts and blocks the agent."""
        make_agent(db_session, budget_daily_usd=10.0, budget_auto_kill=True)
        _add_usage(db_session, "test-agent", 10.5)  # 105%
        result = evaluate_budget(db_session, "test-agent")
        assert result["daily_exceeded"] is True
        assert result["blocked"] is True
        agent = db_session.get(Agent, "test-agent")
        assert agent.status == "budget_blocked"
        assert _count_alerts(db_session, "test-agent", "warning", "daily") == 1
        assert _count_alerts(db_session, "test-agent", "critical", "daily") == 1
        assert _count_alerts(db_session, "test-agent", "exceeded", "daily") == 1

    def test_exceeded_without_auto_kill(self, db_session):
        """Exceeding budget with auto_kill=False should NOT block agent."""
        make_agent(db_session, budget_daily_usd=10.0, budget_auto_kill=False)
        _add_usage(db_session, "test-agent", 11.0)
        result = evaluate_budget(db_session, "test-agent")
        assert result["daily_exceeded"] is True
        assert result["blocked"] is False
        agent = db_session.get(Agent, "test-agent")
        assert agent.status == "running"


# ── Monthly Budget ──────────────────────────────────────────────────

class TestMonthlyBudget:
    def test_monthly_exceeded_blocks(self, db_session):
        """Monthly budget exceeded with auto_kill blocks the agent."""
        make_agent(db_session, budget_monthly_usd=100.0, budget_auto_kill=True)
        _add_usage(db_session, "test-agent", 101.0)
        result = evaluate_budget(db_session, "test-agent")
        assert result["monthly_exceeded"] is True
        assert result["blocked"] is True
        assert _count_alerts(db_session, "test-agent", "exceeded", "monthly") == 1

    def test_monthly_warning_only(self, db_session):
        """Monthly spend at 85% triggers warning but not critical."""
        make_agent(db_session, budget_monthly_usd=100.0, budget_alert_pct=80.0)
        _add_usage(db_session, "test-agent", 85.0)
        evaluate_budget(db_session, "test-agent")
        assert _count_alerts(db_session, "test-agent", "warning", "monthly") == 1
        assert _count_alerts(db_session, "test-agent", "critical", "monthly") == 0


# ── Both Daily and Monthly Budgets ──────────────────────────────────

class TestDualBudgets:
    def test_daily_exceeded_monthly_ok(self, db_session):
        """Only daily budget exceeded blocks when monthly is fine."""
        make_agent(db_session, budget_daily_usd=5.0, budget_monthly_usd=100.0, budget_auto_kill=True)
        _add_usage(db_session, "test-agent", 5.5)
        result = evaluate_budget(db_session, "test-agent")
        assert result["daily_exceeded"] is True
        assert result["monthly_exceeded"] is False
        assert result["blocked"] is True

    def test_both_exceeded(self, db_session):
        """Both budgets exceeded at once."""
        make_agent(db_session, budget_daily_usd=5.0, budget_monthly_usd=5.0, budget_auto_kill=True)
        _add_usage(db_session, "test-agent", 6.0)
        result = evaluate_budget(db_session, "test-agent")
        assert result["daily_exceeded"] is True
        assert result["monthly_exceeded"] is True
        assert result["blocked"] is True
        # Should have alerts for both types
        assert _count_alerts(db_session, "test-agent", "exceeded", "daily") == 1
        assert _count_alerts(db_session, "test-agent", "exceeded", "monthly") == 1


# ── Duplicate Alert Prevention ──────────────────────────────────────

class TestDuplicatePrevention:
    def test_no_duplicate_alerts_on_repeat_evaluation(self, db_session):
        """Repeated evaluations after threshold crossing do not create duplicate alerts."""
        make_agent(db_session, budget_daily_usd=10.0, budget_auto_kill=True)
        _add_usage(db_session, "test-agent", 10.5)

        # First evaluation
        evaluate_budget(db_session, "test-agent")
        assert _count_alerts(db_session, "test-agent", "exceeded", "daily") == 1

        # Subsequent ingests and evaluations
        _add_usage(db_session, "test-agent", 0.5)  # now at 11.0
        evaluate_budget(db_session, "test-agent")
        assert _count_alerts(db_session, "test-agent", "exceeded", "daily") == 1  # still 1

        _add_usage(db_session, "test-agent", 1.0)  # now at 12.0
        evaluate_budget(db_session, "test-agent")
        assert _count_alerts(db_session, "test-agent", "exceeded", "daily") == 1  # still 1

    def test_no_duplicate_warnings(self, db_session):
        """Warning alert is only created once per period."""
        make_agent(db_session, budget_daily_usd=10.0, budget_alert_pct=80.0)
        _add_usage(db_session, "test-agent", 8.5)

        evaluate_budget(db_session, "test-agent")
        evaluate_budget(db_session, "test-agent")
        evaluate_budget(db_session, "test-agent")

        assert _count_alerts(db_session, "test-agent", "warning", "daily") == 1


# ── Period Rollover ─────────────────────────────────────────────────

class TestPeriodRollover:
    def test_daily_rollover_unblocks(self, db_session):
        """Agent blocked by daily budget is unblocked when checked on a new day."""
        make_agent(db_session, budget_daily_usd=10.0, budget_auto_kill=True, status="budget_blocked")

        # Simulate: yesterday's spend was over budget but today's is 0
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        _add_usage(db_session, "test-agent", 15.0, timestamp=yesterday)

        still_blocked, reason = check_agent_budget_blocked(db_session, "test-agent")
        assert still_blocked is False
        agent = db_session.get(Agent, "test-agent")
        assert agent.status == "stopped"  # unblocked to stopped

    def test_monthly_rollover_unblocks(self, db_session):
        """Agent blocked by monthly budget is unblocked when checked in a new month."""
        make_agent(db_session, budget_monthly_usd=100.0, budget_auto_kill=True, status="budget_blocked")

        # Simulate: last month's spend was over budget but this month's is 0
        last_month = datetime.now(timezone.utc).replace(day=1) - timedelta(days=1)
        _add_usage(db_session, "test-agent", 150.0, timestamp=last_month)

        still_blocked, reason = check_agent_budget_blocked(db_session, "test-agent")
        assert still_blocked is False

    def test_still_blocked_same_period(self, db_session):
        """Agent remains blocked if still in the same overspent period."""
        make_agent(db_session, budget_daily_usd=10.0, budget_auto_kill=True, status="budget_blocked")
        _add_usage(db_session, "test-agent", 15.0)  # today's spend

        still_blocked, reason = check_agent_budget_blocked(db_session, "test-agent")
        assert still_blocked is True
        assert "daily budget exceeded" in reason

    def test_check_not_blocked_agent_returns_false(self, db_session):
        """check_agent_budget_blocked on a running agent returns not blocked."""
        make_agent(db_session, budget_daily_usd=10.0, status="running")
        _add_usage(db_session, "test-agent", 15.0)

        still_blocked, reason = check_agent_budget_blocked(db_session, "test-agent")
        assert still_blocked is False


# ── Budget Status ───────────────────────────────────────────────────

class TestBudgetStatus:
    def test_status_ok(self, db_session):
        """Budget status returns correct values for agent under budget."""
        make_agent(db_session, budget_daily_usd=10.0, budget_monthly_usd=100.0)
        _add_usage(db_session, "test-agent", 3.0)

        status = get_agent_budget_status(db_session, "test-agent")
        assert status["daily_spend_usd"] == 3.0
        assert status["daily_budget_usd"] == 10.0
        assert status["daily_pct"] == 30.0
        assert status["daily_state"] == "ok"
        assert status["monthly_state"] == "ok"
        assert status["is_blocked"] is False

    def test_status_exceeded(self, db_session):
        """Budget status correctly reports exceeded state."""
        make_agent(db_session, budget_daily_usd=10.0, status="budget_blocked")
        _add_usage(db_session, "test-agent", 12.0)

        status = get_agent_budget_status(db_session, "test-agent")
        assert status["daily_state"] == "exceeded"
        assert status["daily_pct"] == 120.0
        assert status["is_blocked"] is True

    def test_status_no_budget(self, db_session):
        """Agent with no budgets returns zero percentages."""
        make_agent(db_session, budget_daily_usd=None, budget_monthly_usd=None)
        status = get_agent_budget_status(db_session, "test-agent")
        assert status["daily_pct"] == 0.0
        assert status["monthly_pct"] == 0.0
        assert status["daily_state"] == "ok"
        assert status["monthly_state"] == "ok"

    def test_status_includes_recent_alerts(self, db_session):
        """Budget status includes recently triggered alerts."""
        make_agent(db_session, budget_daily_usd=10.0)
        _add_usage(db_session, "test-agent", 10.5)
        evaluate_budget(db_session, "test-agent")

        status = get_agent_budget_status(db_session, "test-agent")
        assert len(status["recent_alerts"]) == 3  # warning, critical, exceeded

    def test_status_nonexistent_agent(self, db_session):
        """Budget status for nonexistent agent returns empty dict."""
        assert get_agent_budget_status(db_session, "ghost") == {}


# ── Spend Calculation Isolation ─────────────────────────────────────

class TestSpendIsolation:
    def test_daily_spend_only_today(self, db_session):
        """Daily spend only counts today's records."""
        make_agent(db_session)
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        _add_usage(db_session, "test-agent", 50.0, timestamp=yesterday)
        _add_usage(db_session, "test-agent", 3.0)

        assert get_agent_daily_spend(db_session, "test-agent") == 3.0

    def test_monthly_spend_only_this_month(self, db_session):
        """Monthly spend only counts this month's records."""
        make_agent(db_session)
        last_month = datetime.now(timezone.utc).replace(day=1) - timedelta(days=1)
        _add_usage(db_session, "test-agent", 200.0, timestamp=last_month)
        _add_usage(db_session, "test-agent", 7.0)

        assert get_agent_monthly_spend(db_session, "test-agent") == 7.0

    def test_spend_per_agent_isolated(self, db_session):
        """Spend for one agent doesn't pollute another."""
        make_agent(db_session, agent_id="agent-a")
        make_agent(db_session, agent_id="agent-b")
        _add_usage(db_session, "agent-a", 50.0)
        _add_usage(db_session, "agent-b", 3.0)

        assert get_agent_daily_spend(db_session, "agent-a") == 50.0
        assert get_agent_daily_spend(db_session, "agent-b") == 3.0
