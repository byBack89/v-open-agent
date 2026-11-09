# v-open-agent 서버 실행 이미지
# - 의존성만 이미지에 설치한다 (/opt/venv). 소스는 설치하지 않는다.
# - 소스는 실행 시 호스트 폴더를 /workspace 로 공유(bind mount)해서 쓴다.
# - apps/server/pyproject.toml 의 의존성이 바뀌면 `docker compose build` 로 다시 빌드한다.
FROM python:3.11-slim-bookworm AS base

ARG UID=1000
ARG GID=1000

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH=/opt/venv/bin:$PATH \
    VOA_TOOLS=/opt/venv/bin \
    MYPY_CACHE_DIR=/tmp/.mypy_cache \
    RUFF_CACHE_DIR=/tmp/.ruff_cache \
    PYTEST_ADDOPTS="-p no:cacheprovider"

RUN python -m venv /opt/venv

# 서버 의존성 메타데이터는 모든 target이 공유한다.
COPY apps/server/pyproject.toml /tmp/pyproject.toml

# dev와 server target이 같은 비 root 사용자를 사용한다.
RUN groupadd --non-unique -g "${GID}" voa && useradd -m -u "${UID}" -g voa voa

FROM base AS dev
RUN python -c "import tomllib; p = tomllib.load(open('/tmp/pyproject.toml', 'rb'))['project']; o = p.get('optional-dependencies', {}); print('\n'.join(p['dependencies'] + o.get('dev', []) + o.get('server', [])))" > /tmp/requirements.txt \
 && pip install -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt /tmp/pyproject.toml

ENV PYTHONPATH=/workspace/apps/server/src
USER voa
WORKDIR /workspace

FROM base AS server
RUN python -c "import tomllib; p = tomllib.load(open('/tmp/pyproject.toml', 'rb'))['project']; o = p.get('optional-dependencies', {}); print('\n'.join(p['dependencies'] + o.get('server', [])))" > /tmp/requirements.txt \
 && pip install -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt /tmp/pyproject.toml

COPY --chown=voa:voa apps/server/src /opt/voa/src
COPY --chown=voa:voa apps/server/config /opt/voa/config

ENV PYTHONPATH=/opt/voa/src
USER voa
WORKDIR /opt/voa
CMD ["python", "-m", "voa.server"]
