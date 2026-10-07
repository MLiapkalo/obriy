from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel


class LiveResponse(BaseModel):
    status: Literal["ok"]


router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/live")
async def live() -> LiveResponse:
    return LiveResponse(status="ok")
