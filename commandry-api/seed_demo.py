"""Seed demo data for Commandry."""

import os
import random
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import init_db, session_factory
from models import Agent, ExecutionTrace, MCPServer, ProviderPricing, TokenUsage


def seed():
    init_db()

    with session_factory() as db:
        agents = [
            Agent(
                id="code-reviewer",
                display_name="Code Review Agent",
                owner="admin",
                status="running",
                runtime_type="claude-code",
                model_provider="anthropic",
                model_id="claude-sonnet-4-20250514",
                system_prompt="You are a senior code reviewer. Review PRs for bugs, style, and security issues.",
                budget_daily_usd=25.00,
                budget_monthly_usd=500.00,
            ),
            Agent(
                id="pr-summarizer",
                display_name="PR Summarizer",
                owner="admin",
                status="idle",
                runtime_type="api-loop",
                model_provider="anthropic",
                model_id="claude-haiku-4-5-20251001",
                system_prompt="Summarize pull requests concisely.",
                budget_daily_usd=5.00,
                budget_monthly_usd=100.00,
            ),
            Agent(
                id="test-writer",
                display_name="Test Writer Agent",
                owner="admin",
                status="stopped",
                runtime_type="custom",
                model_provider="openai",
                model_id="gpt-4o",
                system_prompt="Generate unit tests for the given code.",
                budget_daily_usd=10.00,
                budget_monthly_usd=200.00,
            ),
            Agent(
                id="doc-generator",
                display_name="Documentation Generator",
                owner="admin",
                status="errored",
                runtime_type="custom",
                model_provider="anthropic",
                model_id="claude-sonnet-4-20250514",
                system_prompt="Generate API documentation from source code.",
                budget_daily_usd=8.00,
                budget_monthly_usd=150.00,
            ),
        ]
        for agent in agents:
            if not db.get(Agent, agent.id):
                db.add(agent)

        servers = [
            MCPServer(
                id="filesystem",
                display_name="Filesystem MCP",
                transport="stdio",
                command="npx -y @modelcontextprotocol/server-filesystem /data",
                status="running",
                tools_cached='["read_file","write_file","list_directory"]',
            ),
            MCPServer(
                id="github",
                display_name="GitHub MCP",
                transport="stdio",
                command="npx -y @modelcontextprotocol/server-github",
                status="running",
                tools_cached='["create_issue","search_repos","get_file_contents"]',
            ),
            MCPServer(
                id="postgres",
                display_name="PostgreSQL MCP",
                transport="stdio",
                command="npx -y @modelcontextprotocol/server-postgres",
                status="stopped",
            ),
        ]
        for server in servers:
            if not db.get(MCPServer, server.id):
                db.add(server)

        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        pricing = [
            ProviderPricing(provider="anthropic", model_id="claude-sonnet-4-20250514", input_price_per_mtok=3.0, output_price_per_mtok=15.0, cache_read_price_per_mtok=0.30, cache_write_price_per_mtok=3.75, effective_date=today),
            ProviderPricing(provider="anthropic", model_id="claude-haiku-4-5-20251001", input_price_per_mtok=0.80, output_price_per_mtok=4.0, cache_read_price_per_mtok=0.08, cache_write_price_per_mtok=1.0, effective_date=today),
            ProviderPricing(provider="anthropic", model_id="claude-opus-4-20250514", input_price_per_mtok=15.0, output_price_per_mtok=75.0, cache_read_price_per_mtok=1.50, cache_write_price_per_mtok=18.75, effective_date=today),
            ProviderPricing(provider="openai", model_id="gpt-4o", input_price_per_mtok=2.50, output_price_per_mtok=10.0, effective_date=today),
            ProviderPricing(provider="openai", model_id="gpt-4o-mini", input_price_per_mtok=0.15, output_price_per_mtok=0.60, effective_date=today),
            ProviderPricing(provider="openai", model_id="o1", input_price_per_mtok=15.0, output_price_per_mtok=60.0, effective_date=today),
            ProviderPricing(provider="openai", model_id="o3-mini", input_price_per_mtok=1.10, output_price_per_mtok=4.40, effective_date=today),
        ]
        for price in pricing:
            db.add(price)

        now = datetime.now(timezone.utc)
        for day_offset in range(7):
            ts = now - timedelta(days=day_offset, hours=random.randint(0, 12))
            for agent_id in ["code-reviewer", "pr-summarizer", "test-writer"]:
                db.add(
                    TokenUsage(
                        agent_id=agent_id,
                        timestamp=ts,
                        provider="anthropic",
                        model_id="claude-sonnet-4-20250514",
                        input_tokens=random.randint(5000, 50000),
                        output_tokens=random.randint(1000, 10000),
                        cost_usd=round(random.uniform(0.05, 2.50), 4),
                    )
                )

        for index in range(5):
            ts = now - timedelta(hours=index * 4)
            db.add(
                ExecutionTrace(
                    id=f"tr_{index:04d}",
                    agent_id="code-reviewer",
                    triggered_by="manual" if index % 2 == 0 else "schedule",
                    started_at=ts,
                    ended_at=ts + timedelta(minutes=random.randint(1, 10)),
                    status="completed" if index < 4 else "failed",
                    turns=random.randint(5, 30),
                    input_tokens=random.randint(10000, 80000),
                    output_tokens=random.randint(2000, 15000),
                    cost_usd=round(random.uniform(0.10, 3.00), 4),
                )
            )

        db.commit()
        print("Demo data seeded successfully!")


if __name__ == "__main__":
    seed()
