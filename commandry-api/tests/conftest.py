"""Shared test fixtures — in-memory SQLite database and FastAPI test client."""

import os
import sys

# Ensure commandry-api is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from database import Base, get_db
from main import app
from models import Agent, ProviderPricing


# Use in-memory SQLite with StaticPool so all sessions share the same database
_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = sessionmaker(bind=_engine, autoflush=False, autocommit=False)


@pytest.fixture(autouse=True)
def db_session():
    """Create all tables, yield a session, then drop everything."""
    Base.metadata.create_all(bind=_engine)
    session = _TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=_engine)


@pytest.fixture(autouse=True)
def override_db(db_session):
    """Override FastAPI's get_db dependency with our test session."""
    def _override():
        try:
            yield db_session
        finally:
            pass  # session lifecycle managed by db_session fixture

    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def client():
    """Synchronous test client (uses httpx under the hood)."""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture()
def pricing(db_session):
    """Seed a standard pricing row for anthropic/claude-sonnet-4-20250514."""
    p = ProviderPricing(
        provider="anthropic",
        model_id="claude-sonnet-4-20250514",
        input_price_per_mtok=3.0,
        output_price_per_mtok=15.0,
        cache_read_price_per_mtok=0.3,
        cache_write_price_per_mtok=3.75,
        effective_date="2025-01-01",
    )
    db_session.add(p)
    db_session.commit()
    return p


def make_agent(
    db_session,
    agent_id="test-agent",
    budget_daily_usd=None,
    budget_monthly_usd=None,
    budget_alert_pct=80.0,
    budget_auto_kill=True,
    status="running",
):
    """Helper: create and return an Agent with given budget config."""
    agent = Agent(
        id=agent_id,
        display_name=f"Test Agent {agent_id}",
        owner="admin",
        status=status,
        budget_daily_usd=budget_daily_usd,
        budget_monthly_usd=budget_monthly_usd,
        budget_alert_pct=budget_alert_pct,
        budget_auto_kill=budget_auto_kill,
    )
    db_session.add(agent)
    db_session.commit()
    return agent
