"""RiskDecision/Alert 계약 (SPEC §3.4, §4.8)."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

from voa.contracts.enums import DeliveryState, RiskState, Severity, TextKind
from voa.contracts.types import MODEL_CONFIG, Id, UtcDatetime

SCHEMA_VERSION = "0.1.0"

ReasonCode = Literal[
    "condition_observed",
    "temporal_confirmation_passed",
    "condition_absent_confirmed",
    "episode_closed",
    "input_stale",
    "quality_blocked",
    "track_lost",
    "sensor_down",
    "fresh_evidence_returned",
]


class Alert(BaseModel):
    model_config = MODEL_CONFIG
    alert_id: Id
    text: str
    text_kind: TextKind
    delivery_state: DeliveryState
    valid_until_utc: UtcDatetime | None = None


class RiskDecision(BaseModel):
    model_config = MODEL_CONFIG
    schema_version: Literal["0.1.0"]
    risk_event_id: Id
    session_id: Id
    device_id: Id
    scenario_id: Id
    policy_version: str
    state: RiskState
    previous_state: RiskState | None = None
    severity: Severity | None = None
    evidence_ids: list[Id]
    reason_codes: list[ReasonCode] = Field(min_length=1)
    model_versions: dict[str, str] = Field(default_factory=dict)
    decided_at_utc: UtcDatetime
    alert: Alert | None = None
    fixture_note: str | None = None

    @model_validator(mode="after")
    def _decision_invariants(self) -> "RiskDecision":
        is_warning = self.state == "warning"
        if is_warning != (self.alert is not None):
            raise ValueError("state is warning if and only if alert is present")
        if is_warning and (self.severity is None or not self.evidence_ids):
            raise ValueError("warning requires severity and at least one evidence id")
        if self.alert is not None and self.alert.delivery_state != "queued":
            raise ValueError("an alert embedded in a decision must be queued")
        return self
