"""TASK-01 스캐폴드 검증 (NFR-01, DAT-03)."""

import importlib
import re
import tomllib
from pathlib import Path

import pytest

SERVER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
SUBPACKAGES = [
    "contracts",
    "config",
    "engine",
    "providers",
    "simulator",
    "replay",
    "explain",
    "storage",
    "server",
]


def test_package_imports() -> None:
    voa = importlib.import_module("voa")
    assert voa.__version__


@pytest.mark.parametrize("name", SUBPACKAGES)
def test_subpackages_import(name: str) -> None:
    importlib.import_module(f"voa.{name}")


def _pyproject() -> dict[str, object]:
    with (SERVER_ROOT / "pyproject.toml").open("rb") as f:
        return tomllib.load(f)


def test_monorepo_source_roots_are_separated() -> None:
    assert (REPO_ROOT / "apps" / "server" / "src" / "voa").is_dir()
    assert (REPO_ROOT / "apps" / "android").is_dir()
    assert (REPO_ROOT / "contracts" / "schemas").is_dir()
    assert (REPO_ROOT / "contracts" / "fixtures").is_dir()
    assert not (REPO_ROOT / "src").exists()
    assert not (REPO_ROOT / "tests").exists()


def test_runtime_dependencies_are_spec_stage_a_only() -> None:
    project = _pyproject()["project"]
    assert isinstance(project, dict)
    names = (re.split(r"[<>=!~ ]", str(d), maxsplit=1)[0] for d in project["dependencies"])
    deps = {n.lower() for n in names}
    # SPEC §1: Stage A 런타임 의존성은 이 두 개뿐 (DAT-03: 모델/HTTP 라이브러리 없음)
    assert deps == {"pydantic", "pyyaml"}


def test_model_marker_excluded_by_default() -> None:
    tool = _pyproject()["tool"]
    assert isinstance(tool, dict)
    addopts = tool["pytest"]["ini_options"]["addopts"]
    assert "not model" in addopts
