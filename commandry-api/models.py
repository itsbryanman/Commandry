"""Commandry SQLAlchemy models — 8 tables."""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from database import Base


class Agent(Base):
    __tablename__ = "agents"

    id = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    owner = Column(String, nullable=False, default="admin")
    status = Column(String, nullable=False, default="stopped")
    runtime_type = Column(String, default="custom")
    runtime_pid = Column(Integer, nullable=True)
    runtime_container_id = Column(String, nullable=True)
    model_provider = Column(String, default="anthropic")
    model_id = Column(String, default="claude-sonnet-4-20250514")
    model_fallback = Column(String, nullable=True)
    model_temperature = Column(Float, default=0.3)
    model_max_tokens = Column(Integer, default=8192)
    system_prompt = Column(Text, nullable=True)
    system_prompt_version = Column(Integer, default=1)
    workspace_root = Column(String, nullable=True)
    workspace_max_disk_mb = Column(Integer, default=5000)
    budget_daily_usd = Column(Float, nullable=True)
    budget_monthly_usd = Column(Float, nullable=True)
    budget_alert_pct = Column(Float, default=80)
    budget_auto_kill = Column(Boolean, default=True)
    guardrails_human_in_loop = Column(Text, nullable=True)  # JSON
    guardrails_network_access = Column(Boolean, default=True)
    guardrails_allowed_domains = Column(Text, nullable=True)  # JSON
    guardrails_max_turns = Column(Integer, default=50)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class TokenUsage(Base):
    __tablename__ = "token_usage"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    provider = Column(String, nullable=False)
    model_id = Column(String, nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cache_read_tokens = Column(Integer, default=0)
    cache_write_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0)
    trace_id = Column(String, nullable=True)
    session_id = Column(String, nullable=True)
    metadata_json = Column(Text, nullable=True)


class ProviderPricing(Base):
    __tablename__ = "provider_pricing"

    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String, nullable=False)
    model_id = Column(String, nullable=False)
    input_price_per_mtok = Column(Float, nullable=False)
    output_price_per_mtok = Column(Float, nullable=False)
    cache_read_price_per_mtok = Column(Float, default=0)
    cache_write_price_per_mtok = Column(Float, default=0)
    effective_date = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("provider", "model_id", "effective_date"),
    )


class BudgetAlert(Base):
    __tablename__ = "budget_alerts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=True)
    alert_type = Column(String, nullable=False)
    budget_type = Column(String, nullable=False)
    limit_usd = Column(Float, nullable=True)
    actual_usd = Column(Float, nullable=True)
    triggered_at = Column(DateTime, default=datetime.utcnow)
    acknowledged = Column(Boolean, default=False)


class MCPServer(Base):
    __tablename__ = "mcp_servers"

    id = Column(String, primary_key=True)
    display_name = Column(String, nullable=False)
    transport = Column(String, default="stdio")
    command = Column(String, nullable=True)
    url = Column(String, nullable=True)
    env_vars = Column(Text, nullable=True)  # JSON
    status = Column(String, default="stopped")
    pid = Column(Integer, nullable=True)
    health_check_type = Column(String, default="tool_list")
    health_check_interval_sec = Column(Integer, default=60)
    last_health_check = Column(DateTime, nullable=True)
    last_health_status = Column(String, nullable=True)
    tools_cached = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class MCPToolPermission(Base):
    __tablename__ = "mcp_tool_permissions"

    mcp_server_id = Column(String, ForeignKey("mcp_servers.id"), primary_key=True)
    tool_name = Column(String, primary_key=True)
    permission = Column(String, default="allowed")


class PromptVersion(Base):
    __tablename__ = "prompt_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    version = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    tag = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String, default="admin")


class ExecutionTrace(Base):
    __tablename__ = "execution_traces"

    id = Column(String, primary_key=True)
    agent_id = Column(String, ForeignKey("agents.id"), nullable=False)
    triggered_by = Column(String, default="manual")
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    status = Column(String, default="running")
    turns = Column(Integer, default=0)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost_usd = Column(Float, default=0)
    tools_called = Column(Text, nullable=True)  # JSON
    errors = Column(Text, nullable=True)  # JSON
    metadata_json = Column(Text, nullable=True)
