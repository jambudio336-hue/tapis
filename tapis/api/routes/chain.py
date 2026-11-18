from __future__ import annotations

from fastapi import APIRouter, Depends

from ... import chain
from ..deps import wajib_token

router = APIRouter(prefix="/chain", tags=["chain"], dependencies=[Depends(wajib_token)])


@router.get("/{target_id}/verify")
async def verify(target_id: str):
    return chain.verify(target_id)


@router.post("/{target_id}/anchor")
async def anchor(target_id: str):
    return chain.anchor(target_id)
