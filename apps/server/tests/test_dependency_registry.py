"""TASK-15A: offline dependency registration and license policy (DAT-05, NFR-04)."""

import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

SERVER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
REGISTRY_HEADING = "### 9.1 Python dependency registry"
PERMISSIVE_LICENSES = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "0BSD"}


@dataclass(frozen=True)
class Dependency:
    name: str
    license: str
    default_install: bool
    non_public_api_required: bool


def _normalize_name(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def _direct_dependencies(pyproject: dict[str, Any]) -> set[str]:
    project = pyproject["project"]
    requirements = [*pyproject["build-system"]["requires"], *project["dependencies"]]
    for group in project.get("optional-dependencies", {}).values():
        requirements.extend(group)
    names = set()
    for requirement in requirements:
        match = re.match(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]*)", requirement)
        assert match is not None, f"Invalid dependency requirement: {requirement}"
        names.add(_normalize_name(match[1]))
    return names


def _read_registry(spec: str) -> dict[str, Dependency]:
    assert REGISTRY_HEADING in spec, "SPEC section 9 dependency registry is missing"
    section = spec.split(REGISTRY_HEADING, 1)[1].split("\n### ", 1)[0]
    rows = [line for line in section.splitlines() if line.startswith("|")]
    assert rows[:2] == [
        "| Package | License (SPDX) | Default install | Non-public API required |",
        "|---|---|---|---|",
    ], "Dependency registry header is missing or malformed"
    registry = {}
    for row in rows[2:]:
        cells = [cell.strip() for cell in row.strip("|").split("|")]
        assert len(cells) == 4, f"Malformed dependency registry row: {row}"
        name, license_id, default_install, non_public_api_required = cells
        assert name and license_id, f"Incomplete dependency registry row: {row}"
        assert default_install in {"yes", "no"}, f"Invalid default install value: {row}"
        assert non_public_api_required in {"yes", "no"}, f"Invalid API obligation value: {row}"
        name = _normalize_name(name)
        assert name not in registry, f"Duplicate dependency registration: {name}"
        registry[name] = Dependency(
            name, license_id, default_install == "yes", non_public_api_required == "yes"
        )
    assert registry, "Dependency registry is empty"
    return registry


def _validate_registry(required: set[str], registry: dict[str, Dependency]) -> None:
    missing = required - registry.keys()
    assert not missing, f"Unregistered direct dependencies: {sorted(missing)}"
    for dependency in registry.values():
        if dependency.name in required or dependency.default_install:
            assert dependency.license in PERMISSIVE_LICENSES, (
                f"Non-permissive or unreviewed license: {dependency.name}: {dependency.license}"
            )
            assert not dependency.non_public_api_required, (
                f"Non-public API obligation: {dependency.name}"
            )


def test_pyproject_dependencies_are_registered_and_permissive() -> None:
    with (SERVER_ROOT / "pyproject.toml").open("rb") as source:
        pyproject = tomllib.load(source)
    spec = (REPO_ROOT / "docs" / "02-technical-specification.md").read_text(encoding="utf-8")
    _validate_registry(_direct_dependencies(pyproject), _read_registry(spec))


def test_all_direct_dependency_groups_are_checked() -> None:
    pyproject = {
        "build-system": {"requires": ["build.tool>=1"]},
        "project": {
            "dependencies": ["Runtime_Package[extra]>=1; python_version >= '3.11'"],
            "optional-dependencies": {
                "dev": ["dev-package>=1"],
                "future": ["Future.Package @ https://example.invalid/package.whl"],
            },
        },
    }
    assert _direct_dependencies(pyproject) == {
        "build-tool",
        "runtime-package",
        "dev-package",
        "future-package",
    }


def test_missing_dependency_added_after_review_fails() -> None:
    registry = {"known": Dependency("known", "MIT", True, False)}
    _validate_registry({"known"}, registry)
    with pytest.raises(AssertionError, match="Unregistered direct dependencies.*late-added"):
        _validate_registry({"known", "late-added"}, registry)


@pytest.mark.parametrize(
    "license_id",
    ["AGPL-3.0-only", "AGPL-3.0-or-later", "CC-BY-NC-4.0", "CC-BY-NC-SA-4.0", "unknown"],
)
@pytest.mark.parametrize("direct", [True, False])
def test_restricted_or_unreviewed_default_license_fails(license_id: str, direct: bool) -> None:
    registry = {"restricted": Dependency("restricted", license_id, True, False)}
    with pytest.raises(AssertionError, match="Non-permissive or unreviewed license"):
        _validate_registry({"restricted"} if direct else set(), registry)


@pytest.mark.parametrize("direct", [True, False])
def test_non_public_api_obligation_fails(direct: bool) -> None:
    registry = {"private-api": Dependency("private-api", "MIT", True, True)}
    with pytest.raises(AssertionError, match="Non-public API obligation"):
        _validate_registry({"private-api"} if direct else set(), registry)


def test_optional_direct_dependency_cannot_bypass_policy() -> None:
    registry = {"restricted": Dependency("restricted", "AGPL-3.0-only", False, False)}
    with pytest.raises(AssertionError, match="Non-permissive or unreviewed license"):
        _validate_registry({"restricted"}, registry)


def test_excluded_candidate_is_not_a_default_dependency() -> None:
    registry = {"candidate": Dependency("candidate", "review_required", False, False)}
    _validate_registry(set(), registry)


@pytest.mark.parametrize(
    "rows, error",
    [
        ("", "empty"),
        ("| package | | yes | no |", "Incomplete"),
        ("| package | MIT | maybe | no |", "Invalid default"),
        ("| package | MIT | yes | |", "Invalid API"),
        ("| package | MIT | yes |", "Malformed"),
        ("| My_Package | MIT | yes | no |\n| my.package | MIT | yes | no |", "Duplicate"),
    ],
)
def test_missing_or_malformed_registry_data_fails(rows: str, error: str) -> None:
    spec = (
        f"{REGISTRY_HEADING}\n\n"
        "| Package | License (SPDX) | Default install | Non-public API required |\n"
        "|---|---|---|---|\n"
        f"{rows}\n"
    )
    with pytest.raises(AssertionError, match=error):
        _read_registry(spec)


def test_registry_is_not_inferred_from_other_document_sections() -> None:
    with pytest.raises(AssertionError, match="registry is missing"):
        _read_registry("## 1. Dependencies\npackage(MIT)")
