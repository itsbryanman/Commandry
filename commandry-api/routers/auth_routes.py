"""Auth routes — login / logout / whoami."""

from fastapi import APIRouter, Cookie, HTTPException, Response
from pydantic import BaseModel

from auth import create_session, delete_session, verify_password, validate_session

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = "admin"
    password: str


@router.post("/login")
async def login(body: LoginRequest, response: Response):
    if not verify_password(body.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_session(body.username)
    response.set_cookie(
        key="commandry_session",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=86400,
    )
    return {"ok": True, "username": body.username}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("commandry_session")
    return {"ok": True}


@router.get("/me")
async def whoami(commandry_session: str | None = Cookie(None)):
    if commandry_session:
        sess = validate_session(commandry_session)
        if sess:
            return {"username": sess["username"], "authenticated": True}
    return {"authenticated": False}
