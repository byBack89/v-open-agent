#!/usr/bin/env bash
# 호스트 UID/GID를 사용해 서버 개발 이미지를 빌드한다.
set -euo pipefail
cd "$(dirname "$0")/.."
export VOA_UID="${VOA_UID:-$(id -u)}" VOA_GID="${VOA_GID:-$(id -g)}"
exec docker compose --profile server build "$@"
