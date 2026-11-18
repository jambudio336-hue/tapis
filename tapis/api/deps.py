from __future__ import annotations

from fastapi import Header, HTTPException, status

from .. import config


async def wajib_token(authorization: str = Header(default="")) -> str:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "butuh Bearer token")
    if authorization[7:] != config.TOKEN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "token salah")
    return authorization[7:]
