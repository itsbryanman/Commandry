"""MCP Servers router."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

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
def list_mcp_servers(db: Session = Depends(get_db)):
    result = db.execute(select(MCPServer).order_by(MCPServer.display_name))
    return [_mcp_dict(s) for s in result.scalars().all()]


@router.post("", status_code=201)
def create_mcp_server(body: MCPServerCreate, db: Session = Depends(get_db)):
    existing = db.get(MCPServer, body.id)
    if existing:
        raise HTTPException(status_code=409, detail="MCP server already exists")
    server = MCPServer(**body.model_dump())
    db.add(server)
    db.commit()
    db.refresh(server)
    return _mcp_dict(server)


@router.get("/{server_id}")
def get_mcp_server(server_id: str, db: Session = Depends(get_db)):
    server = db.get(MCPServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    return _mcp_dict(server)


@router.put("/{server_id}")
def update_mcp_server(server_id: str, body: MCPServerUpdate, db: Session = Depends(get_db)):
    server = db.get(MCPServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(server, k, v)
    server.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(server)
    return _mcp_dict(server)


@router.delete("/{server_id}")
def delete_mcp_server(server_id: str, db: Session = Depends(get_db)):
    server = db.get(MCPServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    db.delete(server)
    db.commit()
    return {"ok": True}


@router.post("/{server_id}/start")
def start_mcp_server(server_id: str, db: Session = Depends(get_db)):
    server = db.get(MCPServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    server.status = "running"
    server.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "status": "running"}


@router.post("/{server_id}/stop")
def stop_mcp_server(server_id: str, db: Session = Depends(get_db)):
    server = db.get(MCPServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    server.status = "stopped"
    server.pid = None
    server.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "status": "stopped"}


@router.post("/{server_id}/health-check")
def health_check(server_id: str, db: Session = Depends(get_db)):
    server = db.get(MCPServer, server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP server not found")
    server.last_health_check = datetime.utcnow()
    server.last_health_status = "ok"
    server.updated_at = datetime.utcnow()
    db.commit()
    return {"ok": True, "status": "ok"}
