"""Tests for budget enforcement through the API layer — ingest, agents, traces, dashboard."""

import uuid
from datetime import datetime, timezone, timedelta

import pytest

from models import Agent, BudgetAlert, TokenUsage
from tests.conftest import make_agent


# ── Token Ingest + Budget ───────────────────────────────────────────

class TestIngestBudget:
    def test_ingest_returns_budget_result(self, client, db_session, pricing):
        """Ingest response includes budget evaluation result."""
        make_agent(db_session, budget_daily_usd=10.0)
        resp = client.post("/api/tokens/ingest", json={
            "agent_id": "test-agent",
            "provider": "anthropic",
            "model_id": "claude-sonnet-4-20250514",
            "input_tokens": 1000,
            "output_tokens": 500,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "budget" in data
        assert "daily_spend" in data["budget"]
        assert data["budget"]["blocked"] is False

    def test_ingest_triggers_warning_alert(self, client, db_session, pricing):
        """Large ingest that crosses warning threshold creates alert visible via API."""
        make_agent(db_session, budget_daily_usd=0.01, budget_alert_pct=80.0)

        # Ingest enough to cross 80% of $0.01
        resp = client.post("/api/tokens/ingest", json={
            "agent_id": "test-agent",
            "provider": "anthropic",
            "model_id": "claude-sonnet-4-20250514",
            "input_tokens": 100_000,   # 100K input = $0.30 at $3/Mtok
            "output_tokens": 0,
        })
        assert resp.status_code == 201

        # Check alerts endpoint
        alerts_resp = client.get("/api/budget/alerts")
        assert alerts_resp.status_code == 200
        alerts = alerts_resp.json()
        assert len(alerts) >= 1
        types = [a["alert_type"] for a in alerts if a["agent_id"] == "test-agent"]
        assert "exceeded" in types

    def test_ingest_blocked_agent_rejected(self, client, db_session, pricing):
        """Ingest for a budget-blocked agent returns 429."""
        make_agent(db_session, status="budget_blocked")
        resp = client.post("/api/tokens/ingest", json={
            "agent_id": "test-agent",
            "provider": "anthropic",
            "model_id": "claude-sonnet-4-20250514",
            "input_tokens": 1000,
            "output_tokens": 0,
        })
        assert resp.status_code == 429
        assert "blocked" in resp.json()["detail"].lower()

    def test_ingest_without_agent_no_budget_eval(self, client, db_session, pricing):
        """Ingest without agent_id skips budget evaluation."""
        resp = client.post("/api/tokens/ingest", json={
            "provider": "anthropic",
            "model_id": "claude-sonnet-4-20250514",
            "input_tokens": 1000,
            "output_tokens": 0,
        })
        assert resp.status_code == 201
        assert resp.json()["budget"] == {}


# ── Agent Lifecycle + Budget ────────────────────────────────────────

class TestAgentLifecycle:
    def test_start_blocked_agent_rejected(self, client, db_session):
        """Starting a budget-blocked agent returns 409 if still over budget."""
        make_agent(db_session, budget_daily_usd=10.0, budget_auto_kill=True, status="budget_blocked")
        # Add usage that keeps it over budget
        usage = TokenUsage(
            agent_id="test-agent", provider="anthropic",
            model_id="test", input_tokens=0, output_tokens=0,
            cost_usd=15.0, timestamp=datetime.now(timezone.utc),
        )
        db_session.add(usage)
        db_session.commit()

        resp = client.post("/api/agents/test-agent/start")
        assert resp.status_code == 409
        assert "cannot start" in resp.json()["detail"].lower()

    def test_start_blocked_agent_period_rollover(self, client, db_session):
        """Starting a budget-blocked agent succeeds if the budget period rolled over."""
        make_agent(db_session, budget_daily_usd=10.0, budget_auto_kill=True, status="budget_blocked")
        # Only yesterday's usage — today is clean
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        usage = TokenUsage(
            agent_id="test-agent", provider="anthropic",
            model_id="test", input_tokens=0, output_tokens=0,
            cost_usd=15.0, timestamp=yesterday,
        )
        db_session.add(usage)
        db_session.commit()

        resp = client.post("/api/agents/test-agent/start")
        assert resp.status_code == 200
        assert resp.json()["status"] == "running"

    def test_restart_blocked_agent_rejected(self, client, db_session):
        """Restarting a budget-blocked agent returns 409 if still over budget."""
        make_agent(db_session, budget_daily_usd=10.0, budget_auto_kill=True, status="budget_blocked")
        usage = TokenUsage(
            agent_id="test-agent", provider="anthropic",
            model_id="test", input_tokens=0, output_tokens=0,
            cost_usd=15.0, timestamp=datetime.now(timezone.utc),
        )
        db_session.add(usage)
        db_session.commit()

        resp = client.post("/api/agents/test-agent/restart")
        assert resp.status_code == 409

    def test_get_agent_includes_budget_status(self, client, db_session):
        """GET /api/agents/{id} includes budget_status field."""
        make_agent(db_session, budget_daily_usd=10.0)
        resp = client.get("/api/agents/test-agent")
        assert resp.status_code == 200
        data = resp.json()
        assert "budget_status" in data
        assert "daily_spend_usd" in data["budget_status"]
        assert "is_blocked" in data["budget_status"]

    def test_list_agents_no_budget_status(self, client, db_session):
        """GET /api/agents/ does NOT include budget_status (for performance)."""
        make_agent(db_session)
        resp = client.get("/api/agents")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert "budget_status" not in data[0]


# ── Trace Budget Enforcement ───────────────────────────────────────

class TestTraceBudget:
    def test_trace_blocked_agent_creates_budget_trace(self, client, db_session):
        """Creating a trace for a blocked agent records a budget_blocked trace and returns 429."""
        make_agent(db_session, budget_daily_usd=10.0, budget_auto_kill=True, status="budget_blocked")
        usage = TokenUsage(
            agent_id="test-agent", provider="anthropic",
            model_id="test", input_tokens=0, output_tokens=0,
            cost_usd=15.0, timestamp=datetime.now(timezone.utc),
        )
        db_session.add(usage)
        db_session.commit()

        trace_id = str(uuid.uuid4())
        resp = client.post("/api/traces", json={
            "id": trace_id,
            "agent_id": "test-agent",
            "triggered_by": "test",
        })
        assert resp.status_code == 429
        detail = resp.json()["detail"]
        assert detail["error"] == "BUDGET_EXCEEDED"
        assert detail["trace_id"] == trace_id

        # Verify the trace was actually recorded
        trace_resp = client.get(f"/api/traces/{trace_id}")
        assert trace_resp.status_code == 200
        assert trace_resp.json()["status"] == "budget_blocked"

    def test_trace_filter_by_status(self, client, db_session):
        """Traces can be filtered by status=budget_blocked."""
        make_agent(db_session, budget_daily_usd=10.0, status="budget_blocked")
        usage = TokenUsage(
            agent_id="test-agent", provider="anthropic",
            model_id="test", input_tokens=0, output_tokens=0,
            cost_usd=15.0, timestamp=datetime.now(timezone.utc),
        )
        db_session.add(usage)
        db_session.commit()

        # Create a blocked trace
        trace_id = str(uuid.uuid4())
        client.post("/api/traces", json={
            "id": trace_id,
            "agent_id": "test-agent",
        })

        resp = client.get("/api/traces?status=budget_blocked")
        assert resp.status_code == 200
        blocked_traces = resp.json()
        assert any(t["id"] == trace_id for t in blocked_traces)

    def test_trace_unblocked_agent_succeeds(self, client, db_session):
        """Creating a trace for a non-blocked agent succeeds normally."""
        make_agent(db_session, status="running")
        trace_id = str(uuid.uuid4())
        resp = client.post("/api/traces", json={
            "id": trace_id,
            "agent_id": "test-agent",
            "triggered_by": "test",
        })
        assert resp.status_code == 201
        assert resp.json()["status"] == "running"


# ── Dashboard Stats ─────────────────────────────────────────────────

class TestDashboard:
    def test_dashboard_stats_includes_budget_fields(self, client, db_session):
        """Dashboard stats include agents_blocked and active_alerts."""
        resp = client.get("/api/dashboard/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert "agents_blocked" in data
        assert "active_alerts" in data

    def test_dashboard_blocked_count(self, client, db_session):
        """Dashboard correctly counts blocked agents."""
        make_agent(db_session, agent_id="a1", status="budget_blocked")
        make_agent(db_session, agent_id="a2", status="budget_blocked")
        make_agent(db_session, agent_id="a3", status="running")

        resp = client.get("/api/dashboard/stats")
        data = resp.json()
        assert data["agents_blocked"] == 2
        assert data["agents_total"] == 3

    def test_dashboard_active_alerts_count(self, client, db_session):
        """Dashboard counts unacknowledged alerts."""
        make_agent(db_session)
        now = datetime.now(timezone.utc)
        for i, ack in enumerate([False, False, True]):
            alert = BudgetAlert(
                agent_id="test-agent",
                alert_type="warning",
                budget_type="daily",
                period_key=f"2026-04-{15+i:02d}",  # different periods to avoid unique constraint
                limit_usd=10.0,
                actual_usd=8.5,
                triggered_at=now,
                acknowledged=ack,
            )
            db_session.add(alert)
        db_session.commit()

        resp = client.get("/api/dashboard/stats")
        data = resp.json()
        assert data["active_alerts"] == 2

    def test_dashboard_alerts_endpoint(self, client, db_session):
        """Dashboard alerts endpoint returns recent alerts."""
        make_agent(db_session)
        alert = BudgetAlert(
            agent_id="test-agent",
            alert_type="exceeded",
            budget_type="daily",
            period_key="2026-04-15",
            limit_usd=10.0,
            actual_usd=12.0,
            triggered_at=datetime.now(timezone.utc),
        )
        db_session.add(alert)
        db_session.commit()

        resp = client.get("/api/dashboard/alerts")
        assert resp.status_code == 200
        alerts = resp.json()
        assert len(alerts) == 1
        assert alerts[0]["alert_type"] == "exceeded"
        assert alerts[0]["period_key"] == "2026-04-15"


# ── Budget Status Endpoint ──────────────────────────────────────────

class TestBudgetStatusEndpoint:
    def test_budget_status_endpoint(self, client, db_session):
        """GET /api/budget/status/{agent_id} returns correct budget data."""
        make_agent(db_session, budget_daily_usd=10.0, budget_monthly_usd=100.0)
        usage = TokenUsage(
            agent_id="test-agent", provider="anthropic",
            model_id="test", input_tokens=0, output_tokens=0,
            cost_usd=5.0, timestamp=datetime.now(timezone.utc),
        )
        db_session.add(usage)
        db_session.commit()

        resp = client.get("/api/budget/status/test-agent")
        assert resp.status_code == 200
        data = resp.json()
        assert data["daily_spend_usd"] == 5.0
        assert data["daily_budget_usd"] == 10.0
        assert data["daily_pct"] == 50.0
        assert data["daily_state"] == "ok"
        assert data["monthly_spend_usd"] == 5.0
        assert data["monthly_budget_usd"] == 100.0
        assert data["is_blocked"] is False

    def test_budget_status_404(self, client, db_session):
        """Budget status for nonexistent agent returns 404."""
        resp = client.get("/api/budget/status/ghost")
        assert resp.status_code == 404

    def test_ack_alert(self, client, db_session):
        """Acknowledging an alert marks it acknowledged."""
        make_agent(db_session)
        alert = BudgetAlert(
            agent_id="test-agent",
            alert_type="warning",
            budget_type="daily",
            period_key="2026-04-15",
            limit_usd=10.0,
            actual_usd=8.5,
        )
        db_session.add(alert)
        db_session.commit()
        db_session.refresh(alert)

        resp = client.post(f"/api/budget/alerts/{alert.id}/ack")
        assert resp.status_code == 200

        # Verify acknowledged
        alerts_resp = client.get("/api/budget/alerts")
        acked = [a for a in alerts_resp.json() if a["id"] == alert.id]
        assert acked[0]["acknowledged"] is True


# ── Concurrency / Repeated Ingest Safety ────────────────────────────

class TestConcurrencySafety:
    def test_rapid_ingests_single_alert_set(self, client, db_session, pricing):
        """Multiple rapid ingests that cross threshold produce exactly one alert per type."""
        make_agent(db_session, budget_daily_usd=0.001)

        # Rapid-fire 5 ingests
        for _ in range(5):
            client.post("/api/tokens/ingest", json={
                "agent_id": "test-agent",
                "provider": "anthropic",
                "model_id": "claude-sonnet-4-20250514",
                "input_tokens": 10_000,
                "output_tokens": 0,
            })

        alerts = client.get("/api/budget/alerts").json()
        agent_alerts = [a for a in alerts if a["agent_id"] == "test-agent"]
        daily_exceeded = [a for a in agent_alerts if a["alert_type"] == "exceeded" and a["budget_type"] == "daily"]
        assert len(daily_exceeded) == 1  # exactly one exceeded alert

    def test_spend_accumulates_correctly(self, client, db_session, pricing):
        """Multiple ingests correctly accumulate spend totals."""
        make_agent(db_session, budget_daily_usd=100.0)

        for _ in range(3):
            client.post("/api/tokens/ingest", json={
                "agent_id": "test-agent",
                "provider": "anthropic",
                "model_id": "claude-sonnet-4-20250514",
                "input_tokens": 1_000_000,  # 1M tokens = $3.00
                "output_tokens": 0,
            })

        status = client.get("/api/budget/status/test-agent").json()
        assert abs(status["daily_spend_usd"] - 9.0) < 0.01  # 3 * $3.00
