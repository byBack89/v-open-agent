"""공통 enum (SPEC §3.2)."""

from typing import Literal

SourceKind = Literal[
    "object_detection", "track_state", "sound_event", "asr_transcript", "ocr_text", "health"
]
ClockQuality = Literal["synced", "estimated", "unknown"]
RiskState = Literal["clear", "candidate", "warning", "unknown", "resolved"]
Verdict = Literal["met", "absent", "indeterminate"]
Severity = Literal["notice", "attention"]
TextKind = Literal["approved_template", "validated_explanation"]
DeliveryState = Literal["queued", "sent", "received", "played", "expired", "unknown_delivery"]
TrackQuality = Literal["good", "degraded", "lost"]
MotionClass = Literal["static", "moving", "unknown"]
HealthStatus = Literal["ok", "degraded", "down"]
QualityFlag = Literal[
    "occluded", "camera_motion_uncompensated", "low_light", "frame_dropped", "clock_unreliable"
]
SpeakerRole = Literal["authenticated_user", "untrusted_environment", "unknown"]
