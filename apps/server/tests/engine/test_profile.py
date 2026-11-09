"""TASK-04 profile validation and sanitized loading (ENG-15, INV-10, SPEC 4.9)."""

from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from voa.config.profile_loader import load_profile
from voa.engine.profile import PolicyProfile, ProfileError

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "profiles"
DEFAULT_PROFILE = (
    Path(__file__).resolve().parents[2] / "config" / "profiles" / "indoor_research_v0.yaml"
)


def profile_data() -> dict[str, Any]:
    data: dict[str, Any] = yaml.safe_load((FIXTURES / "valid.yaml").read_text(encoding="utf-8"))
    return data


def test_load_valid_profile_and_default_match_spec() -> None:
    profile = load_profile(FIXTURES / "valid.yaml")
    assert isinstance(profile, PolicyProfile)
    assert profile == load_profile(str(DEFAULT_PROFILE))
    assert profile.profile_id == "indoor_research_v0"
    assert profile.profile_version == 1
    assert profile.params.staleness_ms == 1000
    assert [scenario.id for scenario in profile.scenarios] == [
        "moving_object_in_attention_zone",
        "visible_obstacle_in_corridor",
    ]
    assert profile.scenarios[0].motion_classes == ["moving"]
    assert profile.scenarios[1].motion_classes == []
    assert profile.scenarios[0].warning_text == "전방 이동 물체에 주의하세요."


@pytest.mark.parametrize(
    ("section", "keys"),
    [
        ("root", ["profile_id", "profile_version", "degraded_notice_text", "params", "scenarios"]),
        (
            "params",
            [
                "min_score",
                "roi_min_overlap",
                "confirm_frames",
                "clear_frames",
                "staleness_ms",
                "unknown_after_ms",
                "warning_ttl_ms",
                "window_ms",
                "window_max_items",
            ],
        ),
        (
            "scenario",
            [
                "id",
                "required_kinds",
                "required_streams",
                "labels",
                "motion_classes",
                "roi",
                "blocking_flags",
                "warning_text",
                "severity",
            ],
        ),
    ],
)
def test_every_required_key_is_required(section: str, keys: list[str]) -> None:
    for key in keys:
        data = profile_data()
        target = (
            data
            if section == "root"
            else (data["params"] if section == "params" else data["scenarios"][0])
        )
        del target[key]
        with pytest.raises(ValidationError):
            PolicyProfile.model_validate(data)


@pytest.mark.parametrize("section", ["root", "params", "scenario"])
def test_unknown_keys_are_rejected(section: str) -> None:
    data = profile_data()
    target = (
        data
        if section == "root"
        else (data["params"] if section == "params" else data["scenarios"][0])
    )
    target["unexpected"] = "value"
    with pytest.raises(ValidationError):
        PolicyProfile.model_validate(data)


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("min_score", -0.01),
        ("min_score", 1.01),
        ("min_score", float("nan")),
        ("roi_min_overlap", -0.01),
        ("roi_min_overlap", 1.01),
        ("confirm_frames", 0),
        ("clear_frames", 0),
        ("staleness_ms", 0),
        ("unknown_after_ms", 999),
        ("warning_ttl_ms", 0),
        ("window_ms", 1499),
        ("window_max_items", 0),
    ],
)
def test_parameter_range_violations(key: str, value: Any) -> None:
    data = profile_data()
    data["params"][key] = value
    with pytest.raises(ValidationError):
        PolicyProfile.model_validate(data)


@pytest.mark.parametrize("score", [0.0, 1.0])
def test_inclusive_score_and_timing_boundaries(score: float) -> None:
    data = profile_data()
    data["params"].update(
        min_score=score,
        roi_min_overlap=score,
        confirm_frames=1,
        clear_frames=1,
        staleness_ms=1,
        unknown_after_ms=1,
        warning_ttl_ms=1,
        window_ms=1,
        window_max_items=1,
    )
    profile = PolicyProfile.model_validate(data)
    assert (
        profile.params.staleness_ms == profile.params.unknown_after_ms == profile.params.window_ms
    )


@pytest.mark.parametrize(
    "kinds",
    [
        [],
        ["track_state"],
        ["sound_event"],
        ["track_state", "object_detection"],
        ["object_detection", "object_detection"],
        ["object_detection", "track_state", "health"],
    ],
)
def test_only_spec_kind_combinations_are_allowed(kinds: list[str]) -> None:
    data = profile_data()
    data["scenarios"][0]["required_kinds"] = kinds
    with pytest.raises(ValidationError):
        PolicyProfile.model_validate(data)


@pytest.mark.parametrize(("index", "motion"), [(0, []), (1, ["moving"]), (0, ["invented"])])
def test_motion_classes_match_kind_combination(index: int, motion: list[str]) -> None:
    data = profile_data()
    data["scenarios"][index]["motion_classes"] = motion
    with pytest.raises(ValidationError):
        PolicyProfile.model_validate(data)


@pytest.mark.parametrize(
    "roi",
    [
        [0, 0, 0, 1],
        [0, 1, 1, 0],
        [-0.1, 0, 1, 1],
        [0, 0, 1.1, 1],
        [0, 0, 1],
        [0, 0, float("nan"), 1],
    ],
)
def test_roi_uses_bbox_rules(roi: list[float]) -> None:
    data = profile_data()
    data["scenarios"][0]["roi"] = roi
    with pytest.raises(ValidationError):
        PolicyProfile.model_validate(data)


@pytest.mark.parametrize("text", ["", "   "])
@pytest.mark.parametrize("key", ["warning_text", "degraded_notice_text"])
def test_approved_text_must_not_be_empty(key: str, text: str) -> None:
    data = profile_data()
    target = data if key == "degraded_notice_text" else data["scenarios"][0]
    target[key] = text
    with pytest.raises(ValidationError):
        PolicyProfile.model_validate(data)


def test_scenario_ids_are_unique_and_scenarios_nonempty() -> None:
    data = profile_data()
    data["scenarios"][1]["id"] = data["scenarios"][0]["id"]
    with pytest.raises(ValidationError):
        PolicyProfile.model_validate(data)
    data["scenarios"] = []
    with pytest.raises(ValidationError):
        PolicyProfile.model_validate(data)


@pytest.mark.parametrize(
    ("name", "code"),
    [
        ("missing.yaml", "file_not_found"),
        ("malformed.yaml", "yaml_invalid"),
        ("sequence.yaml", "yaml_invalid"),
    ],
)
def test_error_categories(name: str, code: str) -> None:
    error = load_profile(FIXTURES / name)
    assert isinstance(error, ProfileError)
    assert error.code == code
    assert str(FIXTURES / name) in error.detail


@pytest.mark.parametrize("content", ["", "null", "42", "secret-value", "!!python/object:bad {}"])
def test_empty_scalar_and_unsafe_yaml_are_invalid(tmp_path: Path, content: str) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text(content, encoding="utf-8")
    error = load_profile(path)
    assert isinstance(error, ProfileError)
    assert error.code == "yaml_invalid"


@pytest.mark.parametrize("failure", ["type", "extra", "yaml"])
def test_error_details_never_echo_secrets(tmp_path: Path, failure: str) -> None:
    secret = "secret-token-sensitive-payload"
    path = tmp_path / "private.yaml"
    data = profile_data()
    if failure == "type":
        data["params"]["confirm_frames"] = secret
    elif failure == "extra":
        data[secret] = secret
        data["scenarios"][0][secret] = secret
    path.write_text(
        f"profile_id: [{secret}" if failure == "yaml" else yaml.safe_dump(data), encoding="utf-8"
    )
    error = load_profile(path)
    assert isinstance(error, ProfileError)
    assert error.code == ("yaml_invalid" if failure == "yaml" else "profile_invalid")
    assert secret not in error.detail
    assert secret not in str(error)
    assert str(path) in error.detail
    if failure == "type":
        assert "params.confirm_frames" in error.detail
