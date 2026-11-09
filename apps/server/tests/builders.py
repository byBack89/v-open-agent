"""Validated, deterministic observations and paired vision frames for engine tests."""

from typing import Any

from voa.contracts.enums import ClockQuality, QualityFlag
from voa.contracts.observation import (
    Detection,
    DetectionPayload,
    ModelRef,
    Observation,
    Payload,
    Track,
    TrackPayload,
)
from voa.engine.ports import FixedEpochClock


def build_observation(
    *,
    observation_id: str = "obs_0001",
    session_id: str = "sess_0001",
    device_id: str = "dev_0001",
    stream_id: str = "camera_0",
    seq: int = 0,
    capture_ts_monotonic_ns: int = 0,
    server_received_mono_ns: int = 0,
    clock_quality: ClockQuality = "synced",
    model: ModelRef | None = None,
    quality_flags: frozenset[QualityFlag] = frozenset(),
    payload: Payload | None = None,
) -> Observation:
    return Observation(
        schema_version="0.1.0",
        observation_id=observation_id,
        session_id=session_id,
        device_id=device_id,
        stream_id=stream_id,
        seq=seq,
        capture_ts_monotonic_ns=capture_ts_monotonic_ns,
        received_at_utc=FixedEpochClock().at(server_received_mono_ns),
        server_received_mono_ns=server_received_mono_ns,
        clock_quality=clock_quality,
        model=model,
        quality_flags=quality_flags,
        payload=(
            payload
            if payload is not None
            else DetectionPayload(kind="object_detection", frame_id="frame_0001", detections=[])
        ),
    )


def build_frame(
    *,
    frame_id: str = "frame_0001",
    observation_ids: tuple[str, str] = ("obs_0001", "obs_0002"),
    detections: list[Detection] | None = None,
    tracks: list[Track] | None = None,
    **overrides: Any,
) -> tuple[Observation, Observation]:
    """Return detection then track observations with the same frame and metadata."""
    return (
        build_observation(
            observation_id=observation_ids[0],
            payload=DetectionPayload(
                kind="object_detection",
                frame_id=frame_id,
                detections=detections if detections is not None else [],
            ),
            **overrides,
        ),
        build_observation(
            observation_id=observation_ids[1],
            payload=TrackPayload(
                kind="track_state", frame_id=frame_id, tracks=tracks if tracks is not None else []
            ),
            **overrides,
        ),
    )
