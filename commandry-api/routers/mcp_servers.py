"""MCP Servers router."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from models import MCPServer

router = APIRouter(prefix="/api/mcp-servers", tags=["mcp-servers"])


class MCPServerCreate(BaseModel):
    id: str
    display_name: str
    transport: str = "stdio"
    command: Optional[str] = None
    url: Optional[str] = None
    env_vars: Optional[str] = None
    health_check_type: str = "tool_list"
    health_check_interval_sec: int = 60


class MCPServerUpdate(BaseModel):
    display_name: Optional[str] = None
    transport: Optional[str] = None
    command: Optional[str] = None
    url: Optional[str] = None
    env_vars: Optional[str] = None
    health_check_type: Optional[str] = None
    health_check_interval_sec: Optional[int] = None


def _mcp_dict(s: MCPServer) -> dict:
    return {
        "id": s.id,
        "display_name": s.display_name,
        "transport": s.transport,
        "command": s.command,
        "url": s.url,
        "env_vars": s.env_vars,
        "status": s.status,
        "health_check_type": s.health_check_type,
        "last_health_check": s.last_health_check.isoformat() if s.last_health_check else None,
        "last_health_status": s.last_health_status,
        "tools_cached": s.tools_cached,
        "created_at": s.created_at.isoformat() if s.created_at else None,
    }


@router.get("")
async def list_mcp_servers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MCPServer).order_by(MCPServer.display_name))
    return [_mcp_dict(s) for s in result.scalars().all()]


@router.post("", status_code=201)
async def create_mcp_server(body: MCPServerCreate, db: AsyncSession = Depends(get_db)):
    existing = await db.get(MCPServer, body.id)
    if existing:
        raise HTTPException(status_code=409, detail="MCP server already exists")
    server = MCPServer(**body.model_dump())
    db.add(server)
    await db.commit()
    await db.refresh(server)
    return _mcp_dict(server)


@router.get("/{server_id}")
async def get_mcp_server(server_id: str, db: AsyncSession = Depends(get_db)):
    server = await db.get(MCPServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return _mcp_dict(server)


@router.put("/{server_id}")
async def update_mcp_server(server_id: str, body: MCPServerUpdate, db: AsyncSession = Depends(get_db)):
    server = await db.get(MCPServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(server, k, v)
    server.updated_at = datetime.utcnow()
    await db.commit()
    await db.refresh(server)
    return _mcp_dict(server)


@router.delete("/{server_id}")
async def delete_mcp_server(server_id: str, db: AsyncSession = Depends(get_db)):
    server = await db.get(MCPServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    await db.delete(server)
    await db.commit()
    return {"ok": True}


@router.post("/{server_id}/start")
async def start_mcp_server(server_id: str, db: AsyncSession = Depends(get_db)):
    server = await db.get(MCPServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    server.status = "running"
    server.updated_at = datetime.utcnow()
    await db.commit()
    return {"ok": True, "status": "running"}


@router.post("/{server_id}/stop")
async def stop_mcp_server(server_id: str, db: AsyncSession = Depends(get_db)):
    server = await db.get(MCPServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    server.status = "stopped"
    server.pid = None
    server.updated_at = datetime.utcnow()
    await db.commit()
    return {"ok": True, "status": "stopped"}


@router.post("/{server_id}/health-check")
async def health_check(server_id: str, db: AsyncSession = Depends(get_db)):
    server = await db.get(MCPServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    server.last_health_check = datetime.utcnow()
    server.last_health_status = "ok"
    server.updated_at = datetime.utcnow()
    await db.commit()
    return {"ok": True, "status": "ok"}
