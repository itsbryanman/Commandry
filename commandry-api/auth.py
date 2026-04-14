"""Commandry authentication — session cookies + API key."""

import hmac
import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Cookie, Depends, Header, HTTPException, status

ADMIN_PASS = os.environ.get("COMMANDRY_ADMIN_PASS", "commandry")
_API_KEY_RAW: Optional[str] = None

# In-memory session store (lightweight for single-instance)
_sessions: dict[str, dict] = {}


def init_api_key() -> None:
    global _API_KEY_RAW
    _API_KEY_RAW = os.environ.get("COMMANDRY_API_KEY")


def create_session(username: str) -> str:
    token = secrets.token_urlsafe(32)
    _sessions[token] = {
        "username": username,
        "created": datetime.utcnow().isoformat(),
        "expires": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
    }
    return token


def validate_session(token: str) -> Optional[dict]:
    sess = _sessions.get(token)
    if not sess:
        return None
    if datetime.fromisoformat(sess["expires"]) < datetime.utcnow():
        _sessions.pop(token, None)
        return None
    return sess


def delete_session(token: str) -> None:
    _sessions.pop(token, None)


async def require_auth(
    commandry_session: Optional[str] = Cookie(None),
    x_api_key: Optional[str] = Header(None),
) -> dict:
    """Dependency that enforces authentication."""
    # API key auth — constant-time comparison
    if x_api_key and _API_KEY_RAW:
        if hmac.compare_digest(x_api_key, _API_KEY_RAW):
            return {"username": "api", "method": "api_key"}
    # Session cookie auth
    if commandry_session:
        sess = validate_session(commandry_session)
        if sess:
            return {"username": sess["username"], "method": "session"}
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")


def verify_password(password: str) -> bool:
    return hmac.compare_digest(password, ADMIN_PASS)
