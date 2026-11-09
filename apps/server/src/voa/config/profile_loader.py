"""File I/O boundary for policy profiles (SPEC 4.9, ENG-15)."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from voa.engine.profile import PolicyParams, PolicyProfile, ProfileError, ScenarioProfile

# Unknown-key locations are user input too: never echo them into diagnostics.
_KNOWN_FIELDS = frozenset(
    (*PolicyProfile.model_fields, *PolicyParams.model_fields, *ScenarioProfile.model_fields)
)


def _safe_location(location: tuple[str | int, ...]) -> str:
    return (
        ".".join(
            str(part) if isinstance(part, int) or part in _KNOWN_FIELDS else "[unknown]"
            for part in location
        )
        or "root"
    )


def load_profile(path: str | Path) -> PolicyProfile | ProfileError:
    """Return a validated profile or a failure containing no source values."""
    profile_path = Path(path)
    try:
        source = profile_path.read_text(encoding="utf-8")
    except OSError:
        return ProfileError("file_not_found", str(profile_path))
    except UnicodeError:
        return ProfileError("yaml_invalid", str(profile_path))

    try:
        data = yaml.safe_load(source)
    except yaml.YAMLError as error:
        location = ""
        if isinstance(error, yaml.MarkedYAMLError) and error.problem_mark is not None:
            mark = error.problem_mark
            location = f":line={mark.line + 1},column={mark.column + 1}"
        return ProfileError("yaml_invalid", f"{profile_path}{location}")

    if not isinstance(data, dict):
        return ProfileError("yaml_invalid", f"{profile_path}:root")
    try:
        return PolicyProfile.model_validate(data)
    except ValidationError as error:
        locations = sorted(
            {
                _safe_location(item["loc"])
                for item in error.errors(
                    include_input=False, include_context=False, include_url=False
                )
            }
        )
        return ProfileError("profile_invalid", f"{profile_path}:{','.join(locations)}")
