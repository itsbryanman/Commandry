"""Commandry API — FastAPI backend serving on :10000.

Registers 7 routers and serves the React SPA via a catch-all route.
"""

import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Ensure commandry-api dir is on sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from auth import init_api_key
from database import init_db
from routers import agents, auth_routes, dashboard, mcp_servers, prompts, tokens, traces

SPA_DIR = Path(__file__).resolve().parent.parent / "commandry-theme" / "dist"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    init_api_key()
    yield


app = FastAPI(
    title="Commandry API",
    description="Mission control for your AI agents.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow the Vite dev server during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:10000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ─────────────────────────────────────────────
app.include_router(auth_routes.router)
app.include_router(agents.router)
app.include_router(tokens.router)
app.include_router(mcp_servers.router)
app.include_router(dashboard.router)
app.include_router(prompts.router)
app.include_router(traces.router)


# ── Health check ─────────────────────────────────────────────────
@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "commandry-api"}

# ── Serve React SPA ──────────────────────────────────────────────
_spa_index = SPA_DIR / "index.html"

if SPA_DIR.is_dir():
    # Mount SPA static assets securely via StaticFiles (no user-controlled paths)
    app.mount("/assets", StaticFiles(directory=str(SPA_DIR / "assets")), name="spa-assets")

@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    """Catch-all: return index.html for SPA client-side routing."""
    if _spa_index.is_file():
        return FileResponse(str(_spa_index))
    return JSONResponse(
        {"error": "SPA not built. Run: cd commandry-theme && npm run build"},
        status_code=503,
    )
