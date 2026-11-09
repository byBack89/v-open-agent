"""TASK-03 RiskDecision/Alert 계약 (CON-01, CON-02, ENG-11, ENG-13)."""

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from tests.contracts.snapshot import assert_schema_snapshot
from voa.contracts.decision import Alert, RiskDecision

REPO_ROOT = Path(__file__).resolve().parents[4]
EXAMPLE_PATH = REPO_ROOT / "contracts" / "fixtures" / "risk_event.json"


def decision_dict(**overrides: Any) -> dict[str, Any]:
    decision: dict[str, Any] = {
        "schema_version": "0.1.0",
        "risk_event_id": "risk_0001",
        "session_id": "sess_0001",
        "device_id": "dev_0001",
        "scenario_id": "visible_obstacle_in_corridor",
        "policy_version": "indoor_research_v0@1",
        "state": "warning",
        "previous_state": "candidate",
        "severity": "attention",
        "evidence_ids": ["obs_0001"],
        "reason_codes": ["temporal_confirmation_passed"],
        "model_versions": {"mock-detector": "0"},
        "decided_at_utc": "2026-11-09T03:15:00Z",
        "alert": {
            "alert_id": "alert_0001",
            "text": "전방 통로에 장애물이 보입니다.",
            "text_kind": "approved_template",
            "delivery_state": "queued",
            "valid_until_utc": "2026-11-09T03:15:04Z",
        },
    }
    decision.update(overrides)
    return decision


def test_positive_fixture_is_valid() -> None:
    decision = RiskDecision.model_validate_json(EXAMPLE_PATH.read_text(encoding="utf-8"))
    assert decision.state == "warning"
    assert decision.alert is not None
    assert decision.alert.text_kind == "approved_template"


def test_non_warning_decision_without_alert_is_valid() -> None:
    decision = RiskDecision.model_validate(
        decision_dict(
            state="unknown",
            previous_state="warning",
            severity=None,
            evidence_ids=[],
            reason_codes=["input_stale"],
            alert=None,
        )
    )
    assert decision.alert is None
    assert decision.evidence_ids == []


@pytest.mark.parametrize(
    ("state", "alert"),
    [
        ("warning", None),
        (
            "candidate",
            {
                "alert_id": "alert_0001",
                "text": "전방 통로에 장애물이 보입니다.",
                "text_kind": "approved_template",
                "delivery_state": "queued",
            },
        ),
    ],
)
def test_validator_1_warning_if_and_only_if_alert(state: str, alert: dict[str, Any] | None) -> None:
    with pytest.raises(ValidationError):
        RiskDecision.model_validate(decision_dict(state=state, alert=alert))


@pytest.mark.parametrize(
    ("field", "value"),
    [("severity", None), ("evidence_ids", [])],
)
def test_validator_2_warning_requires_severity_and_evidence(field: str, value: Any) -> None:
    data = decision_dict()
    data[field] = value
    with pytest.raises(ValidationError):
        RiskDecision.model_validate(data)


def test_validator_3_reason_codes_must_not_be_empty() -> None:
    with pytest.raises(ValidationError):
        RiskDecision.model_validate(decision_dict(reason_codes=[]))


def test_validator_4_embedded_alert_must_be_queued() -> None:
    alert = deepcopy(decision_dict()["alert"])
    alert["delivery_state"] = "sent"
    with pytest.raises(ValidationError):
        RiskDecision.model_validate(decision_dict(alert=alert))


def test_unregistered_reason_code_rejected() -> None:
    with pytest.raises(ValidationError):
        RiskDecision.model_validate(decision_dict(reason_codes=["model_says_dangerous"]))


def test_alert_valid_until_is_optional_but_must_be_utc_when_present() -> None:
    without_deadline = deepcopy(decision_dict()["alert"])
    without_deadline.pop("valid_until_utc")
    assert Alert.model_validate(without_deadline).valid_until_utc is None

    non_utc_deadline = deepcopy(without_deadline)
    non_utc_deadline["valid_until_utc"] = "2026-11-09T12:15:04+09:00"
    with pytest.raises(ValidationError):
        Alert.model_validate(non_utc_deadline)


def test_extra_fields_and_non_utc_decision_time_rejected() -> None:
    with pytest.raises(ValidationError):
        RiskDecision.model_validate(decision_dict(distance_m=1.2))
    with pytest.raises(ValidationError):
        RiskDecision.model_validate(decision_dict(decided_at_utc="2026-11-09T12:15:00+09:00"))


def test_models_are_frozen() -> None:
    decision = RiskDecision.model_validate(decision_dict())
    with pytest.raises(ValidationError):
        setattr(decision, "state", "clear")  # noqa: B010 — frozen 모델 대입 시도


def test_schema_snapshots() -> None:
    assert_schema_snapshot(Alert, "alert")
    assert_schema_snapshot(RiskDecision, "risk_decision")


def test_json_serialization_is_stable() -> None:
    decision = RiskDecision.model_validate(decision_dict())
    first = json.loads(decision.model_dump_json())
    second = json.loads(decision.model_dump_json())
    assert first == second
