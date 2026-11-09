"""Validated policy configuration, without file I/O (SPEC 4.9, INV-06)."""

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from voa.contracts.enums import MotionClass, QualityFlag, Severity, SourceKind
from voa.contracts.types import MODEL_CONFIG, BBox, Id, Score

ProfileErrorCode = Literal["file_not_found", "yaml_invalid", "profile_invalid"]


@dataclass(frozen=True)
class ProfileError:
    """Safe failure value passed to the engine instead of a valid profile."""

    code: ProfileErrorCode
    detail: str


class PolicyParams(BaseModel):
    model_config = MODEL_CONFIG

    min_score: Score
    roi_min_overlap: Score
    confirm_frames: int = Field(ge=1)
    clear_frames: int = Field(ge=1)
    staleness_ms: int = Field(gt=0)
    unknown_after_ms: int
    warning_ttl_ms: int = Field(gt=0)
    window_ms: int
    window_max_items: int = Field(ge=1)

    @model_validator(mode="after")
    def _timing_order(self) -> "PolicyParams":
        if self.unknown_after_ms < self.staleness_ms:
            raise ValueError("unknown_after_ms must be >= staleness_ms")
        if self.window_ms < self.unknown_after_ms:
            raise ValueError("window_ms must be >= unknown_after_ms")
        return self


class ScenarioProfile(BaseModel):
    model_config = MODEL_CONFIG

    id: Id
    required_kinds: list[SourceKind]
    required_streams: list[Id]
    labels: list[str]
    motion_classes: list[MotionClass]
    roi: BBox
    blocking_flags: list[QualityFlag]
    warning_text: str = Field(min_length=1)
    severity: Severity

    @field_validator("warning_text")
    @classmethod
    def _nonblank_warning(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("warning_text must not be blank")
        return value

    @model_validator(mode="after")
    def _kind_and_motion_rules(self) -> "ScenarioProfile":
        if self.required_kinds == ["object_detection"]:
            if self.motion_classes:
                raise ValueError("detection scenarios require empty motion_classes")
        elif self.required_kinds == ["object_detection", "track_state"]:
            if not self.motion_classes:
                raise ValueError("track scenarios require motion_classes")
        else:
            raise ValueError("unsupported required_kinds combination")
        return self


class PolicyProfile(BaseModel):
    model_config = MODEL_CONFIG

    profile_id: Id
    profile_version: int
    degraded_notice_text: str = Field(min_length=1)
    params: PolicyParams
    scenarios: list[ScenarioProfile] = Field(min_length=1)

    @field_validator("degraded_notice_text")
    @classmethod
    def _nonblank_notice(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("degraded_notice_text must not be blank")
        return value

    @model_validator(mode="after")
    def _unique_scenario_ids(self) -> "PolicyProfile":
        ids = [scenario.id for scenario in self.scenarios]
        if len(ids) != len(set(ids)):
            raise ValueError("scenario IDs must be unique")
        return self
