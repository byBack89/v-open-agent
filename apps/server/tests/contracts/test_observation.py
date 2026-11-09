"""TASK-02 Observation 계약 (CON-01, CON-02, ENG-01)."""

import json
from datetime import UTC, datetime, timedelta, timezone
from typing import Any

import pytest
from pydantic import ValidationError

from tests.contracts.snapshot import assert_schema_snapshot
from voa.contracts.observation import (
    DetectionPayload,
    HealthPayload,
    Observation,
    ObservationDraft,
    SoundEventPayload,
    TrackPayload,
)

T0 = datetime(2026, 11, 9, 0, 0, 0, tzinfo=UTC)


def obs_dict(**over: Any) -> dict[str, Any]:
    d: dict[str, Any] = {
        "schema_version": "0.1.0",
        "observation_id": "obs_0001",
        "session_id": "sess_a",
        "device_id": "dev_a",
        "stream_id": "camera_0",
        "seq": 0,
        "capture_ts_monotonic_ns": 0,
        "received_at_utc": "2026-11-09T00:00:00Z",
        "server_received_mono_ns": 0,
        "clock_quality": "synced",
        "model": {"id": "mock", "revision": "0"},
        "payload": {
            "kind": "object_detection",
            "frame_id": "f0",
            "detections": [{"label": "obstacle", "bbox": [0.3, 0.5, 0.6, 0.9], "score": 0.9}],
        },
    }
    d.update(over)
    return d


def det_payload(bbox: list[float], score: float = 0.9) -> dict[str, Any]:
    return {
        "kind": "object_detection",
        "frame_id": "f0",
        "detections": [{"label": "x", "bbox": bbox, "score": score}],
    }


# ---- 성공 ----
def test_valid_detection_observation() -> None:
    o = Observation.model_validate(obs_dict())
    assert o.source_kind == "object_detection"
    assert isinstance(o.payload, DetectionPayload)


def test_empty_detections_allowed() -> None:
    """D-03: 객체 0개 프레임도 관측 1개 — '없음'을 확인할 수 있어야 한다."""
    o = Observation.model_validate(
        obs_dict(payload={"kind": "object_detection", "frame_id": "f1", "detections": []})
    )
    assert isinstance(o.payload, DetectionPayload)
    assert o.payload.detections == []


def test_discriminator_selects_payload_type() -> None:
    track = {
        "kind": "track_state",
        "frame_id": "f0",
        "tracks": [
            {
                "track_id": "t1",
                "label": "person",
                "bbox": [0.1, 0.1, 0.2, 0.2],
                "score": 0.7,
                "quality": "good",
                "motion_class": "moving",
                "age_frames": 3,
            }
        ],
    }
    assert isinstance(Observation.model_validate(obs_dict(payload=track)).payload, TrackPayload)
    health = {"kind": "health", "status": "down", "detail_code": "camera_error"}
    o = Observation.model_validate(obs_dict(payload=health))
    assert isinstance(o.payload, HealthPayload)
    assert o.source_kind == "health"


def test_bbox_boundary_values_accepted() -> None:
    Observation.model_validate(obs_dict(payload=det_payload([0.0, 0.0, 1.0, 1.0], 0.0)))
    Observation.model_validate(obs_dict(payload=det_payload([0.0, 0.0, 1.0, 1.0], 1.0)))


# ---- 실패 ----
@pytest.mark.parametrize(
    "bbox",
    [
        [0.5, 0.1, 0.5, 0.2],  # x1 == x2
        [0.6, 0.1, 0.5, 0.2],  # x1 > x2
        [0.1, 0.3, 0.2, 0.3],  # y1 == y2
        [-0.01, 0.1, 0.2, 0.2],
        [0.1, 0.1, 1.01, 0.2],
    ],
)
def test_bbox_invalid_rejected(bbox: list[float]) -> None:
    with pytest.raises(ValidationError):
        Observation.model_validate(obs_dict(payload=det_payload(bbox)))


@pytest.mark.parametrize("score", [-0.001, 1.001])
def test_score_out_of_range_rejected(score: float) -> None:
    with pytest.raises(ValidationError):
        Observation.model_validate(obs_dict(payload=det_payload([0.1, 0.1, 0.2, 0.2], score)))


def test_extra_field_rejected() -> None:
    with pytest.raises(ValidationError):
        Observation.model_validate(obs_dict(extra_field=1))
    bad = det_payload([0.1, 0.1, 0.2, 0.2])
    bad["detections"][0]["distance_m"] = 1.2  # 근거 없는 거리 필드는 계약에 없음
    with pytest.raises(ValidationError):
        Observation.model_validate(obs_dict(payload=bad))


def test_unknown_kind_rejected() -> None:
    with pytest.raises(ValidationError):
        Observation.model_validate(obs_dict(payload={"kind": "imu", "axes": {}}))


def test_kind_payload_mismatch_rejected() -> None:
    # kind 는 track_state 인데 detection 필드 → 거부
    with pytest.raises(ValidationError):
        Observation.model_validate(
            obs_dict(payload={"kind": "track_state", "frame_id": "f0", "detections": []})
        )


@pytest.mark.parametrize("bad_id", ["", "has space", "x" * 129, "한글"])
def test_invalid_id_rejected(bad_id: str) -> None:
    with pytest.raises(ValidationError):
        Observation.model_validate(obs_dict(observation_id=bad_id))


def test_negative_seq_rejected() -> None:
    with pytest.raises(ValidationError):
        Observation.model_validate(obs_dict(seq=-1))


def test_non_utc_or_naive_datetime_rejected() -> None:
    with pytest.raises(ValidationError):
        Observation.model_validate(obs_dict(received_at_utc="2026-11-09T09:00:00+09:00"))
    with pytest.raises(ValidationError):
        Observation.model_validate(obs_dict(received_at_utc="2026-11-09T00:00:00"))


def test_sound_window_order_and_text_length() -> None:
    with pytest.raises(ValidationError):
        SoundEventPayload.model_validate(
            {
                "kind": "sound_event",
                "chunk_id": "c",
                "window_start_ns": 5,
                "window_end_ns": 5,
                "events": [],
            }
        )
    with pytest.raises(ValidationError):
        Observation.model_validate(
            obs_dict(
                payload={
                    "kind": "ocr_text",
                    "frame_id": "f0",
                    "text": "x" * 501,
                    "bbox": [0.1, 0.1, 0.2, 0.2],
                    "language": "ko",
                    "score": 0.5,
                }
            )
        )


def test_models_are_frozen() -> None:
    o = Observation.model_validate(obs_dict())
    with pytest.raises(ValidationError):
        setattr(o, "seq", 5)  # noqa: B010 — frozen 모델 대입 시도


# ---- 결정론 / 변환 ----
def test_quality_flags_serialized_sorted() -> None:
    o = Observation.model_validate(
        obs_dict(quality_flags=["occluded", "camera_motion_uncompensated", "frame_dropped"])
    )
    dumped = json.loads(o.model_dump_json())
    assert dumped["quality_flags"] == ["camera_motion_uncompensated", "frame_dropped", "occluded"]
    assert dumped["received_at_utc"] == "2026-11-09T00:00:00Z"


def test_unknown_quality_flag_rejected() -> None:
    with pytest.raises(ValidationError):
        Observation.model_validate(obs_dict(quality_flags=["blurry"]))


def test_from_draft_adds_server_fields() -> None:
    draft = ObservationDraft.model_validate(
        {
            "stream_id": "camera_0",
            "seq": 3,
            "capture_ts_monotonic_ns": 100,
            "quality_flags": ["occluded"],
            "payload": det_payload([0.1, 0.1, 0.2, 0.2]),
        }
    )
    o = Observation.from_draft(
        draft,
        observation_id="obs_0009",
        session_id="sess_a",
        device_id="dev_a",
        server_received_mono_ns=5_000_000,
        received_at_utc=T0 + timedelta(milliseconds=5),
    )
    assert o.schema_version == "0.1.0"
    assert o.clock_quality == "unknown"  # Draft 기본값
    assert o.model is None
    assert o.quality_flags == frozenset({"occluded"})
    assert o.seq == 3


def test_draft_rejects_server_fields() -> None:
    with pytest.raises(ValidationError):
        ObservationDraft.model_validate(
            {
                "stream_id": "camera_0",
                "seq": 0,
                "capture_ts_monotonic_ns": 0,
                "observation_id": "obs_x",
                "payload": det_payload([0.1, 0.1, 0.2, 0.2]),
            }
        )


def test_from_draft_rejects_non_utc() -> None:
    draft = ObservationDraft.model_validate(
        {
            "stream_id": "camera_0",
            "seq": 0,
            "capture_ts_monotonic_ns": 0,
            "payload": det_payload([0.1, 0.1, 0.2, 0.2]),
        }
    )
    with pytest.raises(ValidationError):
        Observation.from_draft(
            draft,
            observation_id="o",
            session_id="s",
            device_id="d",
            server_received_mono_ns=0,
            received_at_utc=datetime(2026, 1, 1, tzinfo=timezone(timedelta(hours=9))),
        )


# ---- 스냅샷 ----
def test_schema_snapshots() -> None:
    assert_schema_snapshot(Observation, "observation")
    assert_schema_snapshot(ObservationDraft, "observation_draft")
