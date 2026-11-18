from __future__ import annotations

from fastapi import Header, HTTPException, Query, status

from .. import config


async def wajib_token(authorization: str = Header(default=""), t: str = Query(default="")) -> str:
    calon = authorization[7:] if authorization.startswith("Bearer ") else t
    if not calon:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "butuh Bearer token atau ?t=")
    if calon != config.TOKEN:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "token salah")
    return calon
