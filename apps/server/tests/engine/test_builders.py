"""Validated observation and complete frame helpers for later engine tasks."""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from tests.builders import build_frame, build_observation
from voa.contracts.observation import (
    Detection,
    DetectionPayload,
    HealthPayload,
    Track,
    TrackPayload,
)


def test_observation_defaults_are_valid_and_repeatable() -> None:
    first = build_observation()
    assert first.model_dump_json() == build_observation().model_dump_json()
    assert first.observation_id == "obs_0001"
    assert first.session_id == "sess_0001"
    assert first.received_at_utc == datetime(2026, 11, 9, tzinfo=UTC)
    assert isinstance(first.payload, DetectionPayload)
    assert first.payload.detections == []


def test_observation_overrides_keep_capture_and_server_time_distinct() -> None:
    obs = build_observation(
        observation_id="obs_delayed",
        session_id="sess_other",
        stream_id="camera_1",
        seq=4,
        capture_ts_monotonic_ns=1_000,
        server_received_mono_ns=3_000_000_000,
        quality_flags=frozenset({"occluded"}),
        payload=HealthPayload(kind="health", status="down", detail_code="camera_error"),
    )
    assert obs.capture_ts_monotonic_ns == 1_000
    assert obs.server_received_mono_ns == 3_000_000_000
    assert obs.received_at_utc == datetime(2026, 11, 9, tzinfo=UTC) + timedelta(seconds=3)
    assert (obs.observation_id, obs.session_id, obs.stream_id, obs.seq) == (
        "obs_delayed",
        "sess_other",
        "camera_1",
        4,
    )
    assert obs.quality_flags == frozenset({"occluded"})
    assert isinstance(obs.payload, HealthPayload)


def test_observation_builder_preserves_contract_validation() -> None:
    with pytest.raises(ValidationError):
        build_observation(seq=-1)


def test_empty_frame_contains_detection_and_track_observations() -> None:
    detection, track = build_frame(frame_id="frame_empty", seq=7)
    assert detection.observation_id != track.observation_id
    assert detection.seq == track.seq == 7
    assert isinstance(detection.payload, DetectionPayload)
    assert isinstance(track.payload, TrackPayload)
    assert detection.payload.frame_id == track.payload.frame_id == "frame_empty"
    assert detection.payload.detections == []
    assert track.payload.tracks == []


def test_frame_preserves_objects_and_shared_metadata() -> None:
    detection = Detection(label="obstacle", bbox=(0.3, 0.5, 0.6, 0.9), score=0.9)
    track = Track(
        track_id="track_0001",
        label="person",
        bbox=(0.3, 0.5, 0.6, 0.9),
        score=0.9,
        quality="good",
        motion_class="moving",
        age_frames=2,
    )
    observations = build_frame(
        frame_id="frame_2",
        detections=[detection],
        tracks=[track],
        seq=2,
        server_received_mono_ns=2_000_000_000,
        quality_flags=frozenset({"frame_dropped"}),
    )
    det_obs, track_obs = observations
    assert isinstance(det_obs.payload, DetectionPayload)
    assert isinstance(track_obs.payload, TrackPayload)
    assert det_obs.payload.detections == [detection]
    assert track_obs.payload.tracks == [track]
    assert det_obs.server_received_mono_ns == track_obs.server_received_mono_ns == 2_000_000_000
    assert all(obs.quality_flags == frozenset({"frame_dropped"}) for obs in observations)


def test_builder_calls_do_not_share_mutable_payload_lists() -> None:
    first = build_frame()
    second = build_frame()
    assert isinstance(first[0].payload, DetectionPayload)
    assert isinstance(second[0].payload, DetectionPayload)
    assert first[0].payload.detections is not second[0].payload.detections
