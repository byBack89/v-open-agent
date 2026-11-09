"""AST import allowlist for INV-06 / ENG-17; never import inspected modules."""

import ast
from pathlib import Path

import pytest

ALLOWED_ROOTS = frozenset(
    {
        "__future__",
        "dataclasses",
        "typing",
        "collections",
        "enum",
        "math",
        "datetime",
        "re",
        "pydantic",
    }
)
VOA_ROOT = Path(__file__).resolve().parents[2] / "src" / "voa"


def assert_pure_imports(source: str, module_name: str) -> None:
    """Resolve relative imports before comparing every AST import to INV-06."""
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Import | ast.ImportFrom):
            continue
        modules: list[str] = []
        if isinstance(node, ast.Import):
            modules = [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                package = module_name.split(".")[: -node.level]
                base = ".".join(package + ([node.module] if node.module else []))
            else:
                base = node.module or ""
            modules = [base] if node.module else [f"{base}.{alias.name}" for alias in node.names]
        for module in modules:
            allowed = module.split(".")[0] in ALLOWED_ROOTS or any(
                module == package or module.startswith(package + ".")
                for package in ("voa.engine", "voa.contracts")
            )
            assert allowed, f"{module_name}:{node.lineno}: prohibited import {module}"


def test_engine_and_contracts_import_only_allowlisted_modules() -> None:
    for package in ("engine", "contracts"):
        paths = sorted((VOA_ROOT / package).rglob("*.py"))
        assert paths, f"Missing purity scope: {package}"
        for path in paths:
            relative = path.relative_to(VOA_ROOT.parent).with_suffix("")
            name = ".".join(relative.parts)
            assert_pure_imports(path.read_text(encoding="utf-8"), name)


@pytest.mark.parametrize(
    "source",
    [
        "import time",
        "import random",
        "import os",
        "import pathlib",
        "import yaml",
        "import asyncio",
        "import socket",
        "import torch",
        "import openai",
        "from os.path import exists",
        "from voa.config import profile_loader",
        "import voa.engine_extra",
        "from ..storage import sqlite",
        "from .. import providers",
        "import typing, random",
        "def nested():\n    import socket",
        "if False:\n    import random",
    ],
)
def test_prohibited_import_makes_guard_fail(source: str) -> None:
    with pytest.raises(AssertionError, match="prohibited import"):
        assert_pure_imports(source, "voa.engine.probe")


@pytest.mark.parametrize(
    "source",
    [
        "from __future__ import annotations",
        "from dataclasses import dataclass",
        "from typing import Protocol",
        "from collections.abc import Iterable",
        "import enum, math, datetime, re",
        "from pydantic import BaseModel",
        "from voa.contracts.observation import Observation",
        "import voa.engine.ports",
        "from .ports import IdFactory",
        "from . import ports",
        "from ..contracts import observation",
    ],
)
def test_allowlisted_imports_pass_guard(source: str) -> None:
    assert_pure_imports(source, "voa.engine.probe")
