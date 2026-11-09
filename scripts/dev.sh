#!/usr/bin/env bash
# 호스트에서 실행하는 래퍼. 모든 명령은 컨테이너 안에서 돈다.
#   scripts/dev.sh                 # 전체 검사 (scripts/check.sh)
#   scripts/dev.sh pytest -q apps/server/tests/contracts
#   scripts/dev.sh bash            # 컨테이너 셸
set -euo pipefail
cd "$(dirname "$0")/.."
export VOA_UID="${VOA_UID:-$(id -u)}" VOA_GID="${VOA_GID:-$(id -g)}"
if [ "$#" -eq 0 ]; then set -- scripts/check.sh; fi
exec docker compose run --rm --build dev "$@"
