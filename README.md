# v-open-agent — 근거 기반 실시간 위험 판단 엔진

> **상태**: 설계 v0.4 (2026-11-09), Stage A 구현 진행 중(TASK-01~03 DONE, 다음 TASK-04), 성능 측정치 없음
> 구성도/데이터 흐름도: https://claude.ai/artifact/1fPRdQ942J79ospLMbnRX1 (비공개, 공유 필요)
> 연구/보조 경고용이며, 인증된 산업안전 보호장치나 응급 시스템을 대체하지 않는다.

## 무엇을 만드는가

스마트글래스(또는 시뮬레이터)가 **로컬 엣지 서버에 직접 연결**한다. 서버의 **판단 엔진**은 영상/음향/센서 관측을 시간 축 위에서 평가한다. 그리고 다음 둘 중 하나를 내보낸다.

- **근거 ID가 붙은 위험 경고**
- **"판단 불가(unknown)"**

```
관측(Observation) ──▶ 판단 엔진 ──▶ 결정(RiskDecision) ──▶ 경고 / unknown
  mock → 실모델        ★ 핵심          근거/규칙/버전 포함      템플릿 문구
```

## 방향 (요약)

1. **판단 엔진이 핵심이다.** 서버의 결정론적 엔진만 위험을 판단한다. VLM 같은 생성 모델은 이미 확정된 결정을 설명할 때만 쓰고, 그 설명도 검증을 통과해야 한다.
2. **unknown ≠ clear.** 입력이 끊기거나 가려지거나 오래되면 "안전"이 아니라 "판단 불가"로 처리한다.
3. **엔진 먼저, 모델 나중.** GPU와 가중치 없이 mock 관측과 리플레이로 엔진을 완성한 다음 서버를 붙이고, 실모델은 그 뒤에 붙인다.
4. **로컬/프라이버시.** 외부 API를 쓰지 않고 원본 미디어를 저장하지 않으며, 허용적 라이선스만 쓴다.

## 문서

| 문서 | 내용 |
|---|---|
| [`docs/01-product-requirements.md`](docs/01-product-requirements.md) | 목표(G1~G5) → 요구사항(ENG/CON/INP/EXP/COM/DAT/NFR) → 수용 기준, 테스트 시나리오 T-R, 미결정 사항 |
| [`docs/02-technical-specification.md`](docs/02-technical-specification.md) | 설계: 데이터 계약, **판단 엔진 6단계/불변식/전이표/profile**, 설명 검증, 서버/전송, 저장/보안, 모델 후보 |
| [`docs/03-collaboration-architecture.md`](docs/03-collaboration-architecture.md) | 모듈 경계, 허용 의존, Lane 소유권, 병렬 개발과 통합 순서 |
| [`docs/04-implementation-plan.md`](docs/04-implementation-plan.md) | 요구사항에서 도출한 작업 단위, 상태, 선행 조건, 수용 테스트 |
| [`docs/05-android-client-plan.md`](docs/05-android-client-plan.md) | Android 참조 클라이언트 구조, 작업 패키지, 보안, E2E 검증 계획 |
| [`docs/adr/`](docs/adr/) | 핵심 설계 결정, 기각한 대안, 검증 근거 |
| [`AGENTS.md`](AGENTS.md) / [`CLAUDE.md`](CLAUDE.md) | 코딩 에이전트 규칙 (Codex / Claude Code) |
| [`contracts/fixtures/risk_event.json`](contracts/fixtures/risk_event.json) | RiskDecision 공유 계약 fixture |

## 저장소 구조

```text
apps/server/     Python 판단 엔진과 API 서버
apps/android/    Android 참조 클라이언트
contracts/       양쪽이 공유하는 JSON Schema와 fixture
docs/            요구사항, 명세, 아키텍처, 구현 계획
docker/          서버 컨테이너 정의
scripts/         루트 개발과 검증 명령
```

## 시작하기

현재 Stage A 계약 구현이 진행 중이다. 구현은 `docs/04-implementation-plan.md`의 Task를 **한 번에 하나씩** 진행하고, 병렬 작업은 `docs/03-collaboration-architecture.md`의 Lane 소유권을 따른다.

- **Claude Code**: 저장소 루트에서 `claude`를 실행하고 `/task`를 입력한다(다음 TODO Task를 자동 선택). 특정 Task는 `/task TASK-07`처럼 지정한다. 점검은 `/audit`.
- **Codex**: `docs/04-implementation-plan.md` §5의 공통 프롬프트 + `04-implementation-plan.md의 선행 Task가 DONE인 첫 TODO를 구현하라.`

첫 마일스톤 **MVP-1**(Stage A+B): GPU 없이 시뮬레이터 → 서버 → 판단 엔진 → 경고 전달까지 끝에서 끝까지 시연한다.

## 개발 환경 (Docker)

소스는 호스트에서 편집하고, 빌드/검사/서버 실행은 도커 컨테이너 안에서 한다. `dev` target은 저장소를 mount하고, `server` target은 `apps/server/src`와 runtime config만 이미지에 포함하여 Android 소스를 배포 이미지에서 분리한다.

```bash
scripts/build.sh                           # 서버 개발 이미지 수동 빌드
scripts/dev.sh                             # 전체 검사 (ruff/mypy/pytest)
scripts/dev.sh bash                        # 컨테이너 셸
docker compose --profile server up server  # 서버 (TASK-16 이후)
```

## 기술 기반 (제안)

Python 3.11+ (server import 패키지 `voa`), Pydantic v2, FastAPI(WebSocket), SQLite, pytest/ruff/mypy --strict. 서버 소스는 `apps/server`, Android 소스는 `apps/android`, 공유 JSON 계약은 `contracts`에 둔다. 세부 확정값은 `docs/02-technical-specification.md` §1.

## 라이선스

Apache-2.0을 제안한다. 공개 전에 저작권자를 확인하고 `LICENSE`/`NOTICE`를 작성해야 한다. 타사 모델/코드/데이터는 원래 라이선스를 따른다.
