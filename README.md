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

**Agent Management** — Register, configure, and control AI agents with per-agent model selection, budget limits, and workspace isolation. Start, stop, and restart agents as real subprocesses with PID tracking and log capture.

**MCP Server Registry** — Connect and monitor Model Context Protocol servers. Health checks, tool discovery, per-tool permission controls, and a visual tool browser across all connected servers.

**Token and Cost Tracking** — Real-time token usage ingestion with automatic cost computation from provider pricing tables. Daily and monthly budget enforcement with alerts and auto-kill on overspend. The cost dashboard answers "which agent is burning the most money" at a glance.

**Prompt Versioning** — Git-style version control for system prompts. Every edit creates a new version. Unified diff viewer between any two versions. One-click rollback. Tag versions as production, staging, or draft.

**Execution Traces** — Structured traces of agent runs with step-by-step timelines. Expand any tool call to see its input, output, latency, and which MCP server handled it. Filter by agent, status, date range, or cost.

**System Administration** — File manager, process viewer, cron editor, service management, web terminal, and system status dashboard inherited from a proven sysadmin foundation. The host infrastructure and the agent layer managed from the same panel.

**Dashboard** — Four stat cards, agent status grid, weekly spend chart, MCP server health, and recent alerts. Everything important on one screen.

---

## Architecture

```
                          :10000
                            |
                    +-------+-------+
                    |   FastAPI     |
                    |   (Python)   |
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
| Backend | FastAPI, SQLAlchemy, aiosqlite, Pydantic |
| Database | SQLite (embedded, zero config) |
| Container | Ubuntu 24.04, single Dockerfile |

```
commandry-api/        FastAPI backend — models, routers, schemas, seeders
commandry-theme/      React SPA — pages, components, API client
bin/                  Startup and CLI scripts
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

## API Reference

All routes are prefixed with `/api`. Responses are JSON.

### Core

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/health` | Health check |
| `POST` | `/api/auth/login` | Authenticate (returns session cookie) |
| `GET` | `/api/dashboard/stats` | Dashboard summary statistics |
| `GET` | `/api/dashboard/alerts` | Recent budget alerts |

### Agents

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/agents` | List all agents |
| `POST` | `/api/agents` | Create agent |
| `GET` | `/api/agents/{id}` | Agent detail |
| `PUT` | `/api/agents/{id}` | Update agent |
| `DELETE` | `/api/agents/{id}` | Delete agent |
| `POST` | `/api/agents/{id}/start` | Start agent process |
| `POST` | `/api/agents/{id}/stop` | Stop agent process |
| `GET` | `/api/agents/{id}/logs` | Tail agent process logs |

### Tokens and Cost

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/tokens/ingest` | Record token usage |
| `GET` | `/api/tokens/summary` | Cost totals (today, week, month) |
| `GET` | `/api/tokens/by-agent/{id}` | Per-agent usage history |
| `GET` | `/api/tokens/timeseries` | Cost over time for charts |

### MCP Servers

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/mcp-servers` | List MCP servers |
| `POST` | `/api/mcp-servers` | Register MCP server |
| `GET` | `/api/mcp-servers/{id}` | Server detail |
| `POST` | `/api/mcp-servers/{id}/start` | Start server |
| `POST` | `/api/mcp-servers/{id}/stop` | Stop server |
| `POST` | `/api/mcp-servers/{id}/health-check` | Trigger health check |

### Prompts

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/agents/{id}/prompts` | List prompt versions |
| `POST` | `/api/agents/{id}/prompts` | Create new version |
| `GET` | `/api/agents/{id}/prompts/diff/{v1}/{v2}` | Diff two versions |
| `POST` | `/api/agents/{id}/prompts/{ver}/rollback` | Rollback to version |

### Traces

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/traces` | List traces (filterable) |
| `GET` | `/api/traces/{id}` | Trace detail with steps |
| `POST` | `/api/traces` | Create trace |
| `POST` | `/api/traces/{id}/steps` | Add trace step |

---

## Project Structure

```
commandry-api/
  main.py              Application entry point, SPA serving, lifespan
  models.py            SQLAlchemy models (8 tables)
  schemas.py           Pydantic request/response schemas
  database.py          Async SQLite engine and session factory
  seed.py              Provider pricing seed data
  seed_demo.py         Demo data for first-run experience
  routers/
    agents.py          Agent CRUD and lifecycle
    tokens.py          Token ingestion, cost computation, timeseries
    mcp_servers.py     MCP server registry and health
    prompts.py         Prompt versioning and diffs
    traces.py          Execution trace recording
    dashboard.py       Aggregate stats and alerts
    pricing.py         Provider pricing management

commandry-theme/
  src/
    pages/
      Dashboard.tsx    Overview with stat cards, agent grid, spend chart
      AgentList.tsx    Agent card grid with status badges
      AgentDetail.tsx  Tabbed agent config (model, prompt, budget, logs)
      AgentCreate.tsx  New agent wizard
      CostDashboard.tsx  Token spend breakdown and trends
      MCPServers.tsx   Server cards with health indicators
      Prompts.tsx      Version history, editor, diff viewer
      Traces.tsx       Filterable trace table with step timeline
    components/
      Sidebar.tsx      Collapsible dark navigation
      StatusBadge.tsx  Color-coded status pills
      Loading.tsx      Spinner
      EmptyState.tsx   Empty page placeholder with CTA
    lib/
      api.ts           Typed fetch client for all endpoints
      types.ts         TypeScript interfaces
```

---


---

## License

Commandry is **free for personal and non-commercial use**.

Commercial use (companies, agencies, consultancies, or any revenue-generating activity) requires a paid license. See [LICENCE](LICENCE) for full terms.

For commercial licensing inquiries: dev@backwoodsdevelopment.com