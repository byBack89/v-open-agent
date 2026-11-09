"""공통 제약 타입 (SPEC §3.1)."""

from datetime import datetime, timedelta
from typing import Annotated

from pydantic import AfterValidator, AwareDatetime, ConfigDict, Field, StringConstraints

MODEL_CONFIG = ConfigDict(extra="forbid", frozen=True)

Id = Annotated[str, StringConstraints(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9_.:-]+$")]
Score = Annotated[float, Field(ge=0.0, le=1.0)]


def _check_bbox(v: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    x1, y1, x2, y2 = v
    if not (0.0 <= x1 < x2 <= 1.0 and 0.0 <= y1 < y2 <= 1.0):
        raise ValueError("bbox must satisfy 0<=x1<x2<=1 and 0<=y1<y2<=1")
    return v


BBox = Annotated[tuple[float, float, float, float], AfterValidator(_check_bbox)]


def _check_utc(v: datetime) -> datetime:
    if v.utcoffset() != timedelta(0):
        raise ValueError("datetime must be UTC")
    return v


UtcDatetime = Annotated[AwareDatetime, AfterValidator(_check_utc)]
