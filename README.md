# Commandry

**Mission control for your AI agents.**

[![License: Personal Free / Commercial Paid](https://img.shields.io/badge/license-personal%20free%20%7C%20commercial%20paid-blue)](LICENCE)
[![Docker](https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white)](Dockerfile)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-3776AB?logo=python&logoColor=white)](commandry-api/)
[![React 19](https://img.shields.io/badge/react-19-61DAFB?logo=react&logoColor=black)](commandry-theme/)
[![TypeScript](https://img.shields.io/badge/typescript-strict-3178C6?logo=typescript&logoColor=white)](commandry-theme/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.115-009688?logo=fastapi&logoColor=white)](commandry-api/)
[![SQLite](https://img.shields.io/badge/sqlite-embedded-003B57?logo=sqlite&logoColor=white)](commandry-api/)

---

Commandry is a self-hosted admin panel for managing AI agents, MCP servers, token budgets, prompt versions, and execution traces. One port, one container, one dashboard.

Built for solo developers and small teams running Claude Code, custom agents, or any LLM-backed automation on their own infrastructure.

---

## Features

**Agent Management** - Register, configure, and control AI agents with per-agent model selection, budget limits, and workspace isolation. Start, stop, and restart agents with status tracking.

**MCP Server Registry** - Connect and monitor Model Context Protocol servers. Health checks, tool discovery, per-tool permission controls across all connected servers.

**Token and Cost Tracking** - Real-time token usage ingestion with automatic cost computation from provider pricing tables. Per-agent and per-model cost breakdowns. The dashboard answers "which agent is burning the most money" at a glance.

**Budget Enforcement** - Daily and monthly budget limits per agent with three-tier threshold alerts (warning, critical, exceeded) and automatic agent blocking on overspend. Budget periods use UTC. Agents blocked by budget are automatically unblocked when the period rolls over. See [Budget Enforcement](#budget-enforcement) for details.

**Prompt Versioning** - Version control for system prompts. Every edit creates a new version with tagging support.

**Execution Traces** - Structured traces of agent runs with token counts, cost, and status tracking. Budget-blocked executions are recorded as distinct `budget_blocked` traces with structured error codes for auditability.

**Dashboard** - Stat cards (agents running, today's cost, budget alerts, MCP servers), agent status grid, and recent budget alerts table. Blocked agents are visually distinct with orange borders and shield icons.

---

## Architecture

```
                          :10000
                            |
                    +-------+-------+
                    |   FastAPI     |
                    |   (Python)    |
                    +---+-----+----+
                        |     |
               /api/*   |     |   /*
                        v     v
              +---------+   +-----------+
              | SQLite  |   | React SPA |
              | Backend |   | (static)  |
              +---------+   +-----------+
```

| Layer | Stack |
|-------|-------|
| Frontend | React 19, Vite, Tailwind CSS, TypeScript |
| Backend | FastAPI, SQLAlchemy (synchronous), Pydantic |
| Database | SQLite (embedded, zero config) |
| Container | Ubuntu 24.04, single Dockerfile |

```
commandry-api/        FastAPI backend - models, routers, services
commandry-theme/      React SPA - pages, components, API client
Dockerfile            Single-stage container build
docker-compose.yml    One-command deployment
```

---

## Quick Start

### Docker (recommended)

```bash
docker build -t commandry .
docker run -d \
  --name commandry \
  -p 10000:10000 \
  -v commandry-data:/data \
  -e COMMANDRY_ADMIN_PASS=your-password \
  commandry
```

Open [http://localhost:10000](http://localhost:10000).

### Docker Compose

```yaml
services:
  commandry:
    build: .
    ports:
      - "10000:10000"
    volumes:
      - commandry-data:/data
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - COMMANDRY_ADMIN_PASS=your-password
    restart: unless-stopped

volumes:
  commandry-data:
```

```bash
docker compose up -d
```

### Local Development

```bash
# Backend
cd commandry-api
pip install -r requirements.txt
COMMANDRY_DB=/tmp/commandry.db uvicorn main:app --reload --port 10000

# Frontend (separate terminal)
cd commandry-theme
npm install
npm run dev
```

The Vite dev server proxies `/api/*` to `localhost:10000` automatically.

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `COMMANDRY_DATA` | `/data` | Root data directory |
| `COMMANDRY_DB` | `/data/commandry/commandry.db` | SQLite database path |
| `COMMANDRY_ADMIN_PASS` | `commandry` | Admin login password |
| `COMMANDRY_SPA_DIR` | `/opt/commandry/commandry-theme/dist` | Path to built SPA assets |

---

## Budget Enforcement

Commandry enforces daily and monthly spending limits per agent. Budget evaluation runs automatically after every token usage ingest.

### Budget Periods (UTC)

| Period | Window | Period Key Format |
|--------|--------|-------------------|
| Daily | Midnight-to-midnight UTC | `YYYY-MM-DD` |
| Monthly | First-of-month midnight UTC | `YYYY-MM` |

### Threshold Levels

| Level | Trigger | Action |
|-------|---------|--------|
| **Warning** | Spend >= `budget_alert_pct`% of limit (default 80%) | Alert created |
| **Critical** | Spend >= 95% of limit | Alert created |
| **Exceeded** | Spend >= 100% of limit | Alert created + agent blocked (if `budget_auto_kill` is true) |

### Behavior

- **Alert deduplication**: Each (agent, alert_type, budget_type, period_key) combination fires at most once. A unique DB constraint prevents duplicates even under concurrent ingests.
- **Auto-kill**: When an agent's budget is exceeded and `budget_auto_kill` is enabled, the agent's status is set to `budget_blocked`. Blocked agents cannot start, restart, create new traces, or ingest new tokens.
- **Period rollover**: Blocked agents are automatically unblocked when checked in a new budget period. The check happens at agent start/restart and trace creation time — no background cron required.
- **Precise math**: Threshold percentages are calculated using Python `Decimal` to avoid floating-point comparison issues.

### Agent Budget Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `budget_daily_usd` | float | null | Daily spending limit in USD. Null = no daily limit. |
| `budget_monthly_usd` | float | null | Monthly spending limit in USD. Null = no monthly limit. |
| `budget_alert_pct` | float | 80 | Warning threshold percentage. |
| `budget_auto_kill` | bool | true | Whether to block the agent on budget exceeded. |

---

## API Reference

All routes are prefixed with `/api`. Responses are JSON.

### Core

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/auth/login` | Authenticate (returns session cookie) |
| `POST` | `/api/auth/logout` | Log out |
| `GET` | `/api/auth/me` | Current user info |
| `GET` | `/api/dashboard/stats` | Dashboard summary (agents running/total/blocked, cost, alerts count) |
| `GET` | `/api/dashboard/alerts` | Recent budget alerts (last 25) |

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/agents` | List all agents |
| `POST` | `/api/agents` | Create agent |
| `GET` | `/api/agents/{id}` | Agent detail (includes `budget_status` object) |
| `PUT` | `/api/agents/{id}` | Update agent |
| `DELETE` | `/api/agents/{id}` | Delete agent |
| `POST` | `/api/agents/{id}/start` | Start agent (rejects if budget-blocked) |
| `POST` | `/api/agents/{id}/stop` | Stop agent |
| `POST` | `/api/agents/{id}/restart` | Restart agent (rejects if budget-blocked) |

### Tokens and Cost

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/tokens/ingest` | Record token usage (triggers budget evaluation) |
| `GET` | `/api/tokens/summary` | Cost totals (today, month, all-time) |
| `GET` | `/api/tokens/by-agent/{id}` | Per-agent usage history (last 100) |
| `GET` | `/api/tokens/by-model` | Aggregate usage by model |

### Budget

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/budget/alerts` | List budget alerts (last 50) |
| `POST` | `/api/budget/alerts/{id}/ack` | Acknowledge an alert |
| `GET` | `/api/budget/status/{agent_id}` | Full budget status for an agent |

The budget status response includes:
- `daily_spend_usd`, `monthly_spend_usd` - current period totals
- `daily_budget_usd`, `monthly_budget_usd` - configured limits
- `daily_pct`, `monthly_pct` - usage percentages
- `daily_state`, `monthly_state` - `ok` / `warning` / `critical` / `exceeded`
- `is_blocked` - whether agent is currently budget-blocked
- `recent_alerts` - last 10 alerts for this agent

### Pricing

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/pricing` | List provider pricing |
| `POST` | `/api/pricing` | Create pricing entry |
| `PUT` | `/api/pricing/{id}` | Update pricing entry |

### MCP Servers

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/mcp-servers` | List MCP servers |
| `POST` | `/api/mcp-servers` | Register MCP server |
| `GET` | `/api/mcp-servers/{id}` | Server detail |
| `PUT` | `/api/mcp-servers/{id}` | Update server |
| `DELETE` | `/api/mcp-servers/{id}` | Delete server |
| `POST` | `/api/mcp-servers/{id}/start` | Start server |
| `POST` | `/api/mcp-servers/{id}/stop` | Stop server |
| `POST` | `/api/mcp-servers/{id}/health-check` | Trigger health check |

### Prompts

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/prompts/{agent_id}` | List prompt versions for agent |
| `POST` | `/api/prompts/{agent_id}` | Create new prompt version |
| `GET` | `/api/prompts/{agent_id}/{version}` | Get specific prompt version |

### Traces

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/traces` | List traces (filter by `agent_id`, `status`) |
| `GET` | `/api/traces/{id}` | Trace detail |
| `POST` | `/api/traces` | Create trace (rejects budget-blocked agents with 429) |
| `PUT` | `/api/traces/{id}` | Update trace |

Budget-blocked trace creation returns HTTP 429 with:
```json
{
  "detail": {
    "error": "BUDGET_EXCEEDED",
    "message": "Agent 'my-agent' is blocked: daily budget exceeded ($12.50 / $10.00)",
    "trace_id": "uuid-of-recorded-trace"
  }
}
```
A `budget_blocked` trace is still recorded for auditability, with structured errors in the `errors` field.

---

## Project Structure

```
commandry-api/
  main.py              Application entry point, SPA serving, lifespan
  models.py            SQLAlchemy models (8 tables)
  database.py          Synchronous SQLite engine and session factory
  budget_service.py    Budget evaluation, threshold alerts, enforcement
  auth.py              Session-based authentication
  routers/
    agents.py          Agent CRUD and lifecycle (with budget checks)
    tokens.py          Token ingestion, cost computation, budget evaluation
    mcp_servers.py     MCP server registry and health
    prompts.py         Prompt versioning
    traces.py          Execution trace recording (with budget enforcement)
    dashboard.py       Aggregate stats and budget alerts
    auth_routes.py     Login, logout, whoami
  tests/
    conftest.py        Shared fixtures (in-memory SQLite, test client)
    test_budget_service.py   Budget service unit tests (25 tests)
    test_api_budget.py       API integration tests (21 tests)

commandry-theme/
  src/
    pages/
      Dashboard.tsx    Overview with stat cards, agent grid, budget alerts table
      Agents.tsx       Agent card grid with status badges and blocked indicators
      AgentDetail.tsx  Tabbed agent view (overview, config, prompt, budget)
    components/
      Sidebar.tsx      Navigation sidebar
      StatusBadge.tsx  Color-coded status pills (includes budget_blocked, warning, critical, exceeded)
      StatCard.tsx     Dashboard stat card component
    lib/
      api.ts           Typed fetch client for all endpoints with full type definitions
```

---

## Testing

```bash
cd commandry-api
pip install -r requirements.txt
pip install pytest httpx
python -m pytest tests/ -v
```

46 tests covering:
- Budget evaluation at all threshold levels (below, warning, critical, exceeded)
- Duplicate alert prevention across repeated ingests
- Daily and monthly budgets (individually and combined)
- Agent blocking and period rollover unblocking
- API-level enforcement (ingest rejection, start/restart rejection, trace blocking)
- Dashboard stats accuracy (blocked count, active alerts count)
- Budget status endpoint correctness
- Concurrency safety (rapid ingests produce exactly one alert set)

---

## License

Commandry is **free for personal and non-commercial use**.

Commercial use (companies, agencies, consultancies, or any revenue-generating activity) requires a paid license. See [LICENCE](LICENCE) for full terms.

For commercial licensing inquiries: dev@backwoodsdevelopment.com
