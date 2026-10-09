from asyncio import timeout
from time import perf_counter
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from obriy_api.db import DbProbe, get_db_probe


class LiveResponse(BaseModel):
    status: Literal["ok"]


class CheckResult(BaseModel):
    status: Literal["ok", "error"]
    latency_ms: float
    detail: str | None


class Checks(BaseModel):
    db: CheckResult


class ReadinessResponse(BaseModel):
    status: Literal["ok", "degraded"]
    checks: Checks


router = APIRouter(prefix="/api/health", tags=["health"])


def _elapsed_ms(start: float, end: float) -> float:
    return (end - start) * 1000


def get_db_check_timeout() -> float:
    return 1.0


async def run_check(probe: DbProbe, timeout_s: float) -> CheckResult:
    start = perf_counter()
    try:
        async with timeout(timeout_s):
            await probe()
    except TimeoutError:
        return CheckResult(
            status="error",
            latency_ms=_elapsed_ms(start, perf_counter()),
            detail=f"timed out after {timeout_s}s",
        )
    except Exception as exc:
        return CheckResult(status="error", latency_ms=_elapsed_ms(start, perf_counter()), detail=type(exc).__name__)
    return CheckResult(status="ok", latency_ms=_elapsed_ms(start, perf_counter()), detail=None)


@router.get("", responses={503: {"model": ReadinessResponse}})
async def ready(
    response: Response,
    db_probe: Annotated[DbProbe, Depends(get_db_probe)],
    timeout_s: Annotated[float, Depends(get_db_check_timeout)],
) -> ReadinessResponse:
    db = await run_check(db_probe, timeout_s)
    if db.status == "error":
        response.status_code = 503
        return ReadinessResponse(status="degraded", checks=Checks(db=db))
    return ReadinessResponse(status="ok", checks=Checks(db=db))


@router.get("/live")
async def live() -> LiveResponse:
    return LiveResponse(status="ok")
