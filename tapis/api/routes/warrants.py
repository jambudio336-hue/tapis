from __future__ import annotations

from fastapi import APIRouter, Depends

from ...core import warrant as wr
from ..deps import wajib_token

router = APIRouter(prefix="/warrants", tags=["warrants"], dependencies=[Depends(wajib_token)])


@router.get("/kedaluwarsa")
async def jalankan_ttl():
    return {"ditutup": wr.kedaluwarsa()}


@router.get("/peringatan")
async def peringatan():
    return wr.hampir_habis()
