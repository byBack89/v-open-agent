"""JSON Schema 스냅샷 헬퍼 (CON-02). 갱신: VOA_UPDATE_SNAPSHOTS=1 pytest"""

import json
import os
from pathlib import Path

from pydantic import BaseModel

REPO_ROOT = Path(__file__).resolve().parents[4]
SNAP_DIR = REPO_ROOT / "contracts" / "schemas"


def assert_schema_snapshot(model: type[BaseModel], name: str) -> None:
    current = json.dumps(model.model_json_schema(), ensure_ascii=False, indent=2, sort_keys=True)
    path = SNAP_DIR / f"{name}.schema.json"
    if os.environ.get("VOA_UPDATE_SNAPSHOTS") == "1" or not path.exists():
        if not path.exists() and os.environ.get("VOA_UPDATE_SNAPSHOTS") != "1":
            raise AssertionError(f"snapshot missing: {path}. Run with VOA_UPDATE_SNAPSHOTS=1")
        path.write_text(current + "\n", encoding="utf-8")
        return
    expected = path.read_text(encoding="utf-8").rstrip("\n")
    assert current == expected, f"schema changed for {name}: bump version and update snapshot"
