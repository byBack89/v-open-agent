#!/usr/bin/env bash
# 단일 검증 명령 (SPEC §1). 도커 컨테이너 안에서 실행한다: scripts/dev.sh
# VOA_TOOLS: 도구 경로 (컨테이너는 /opt/venv/bin, 이미지에서 설정)
set -euo pipefail
cd "$(dirname "$0")/../apps/server"
V="${VOA_TOOLS:?VOA_TOOLS not set — run inside the container: scripts/dev.sh}"
"$V/ruff" check src tests
"$V/ruff" format --check src tests
"$V/mypy"
"$V/pytest" -q
