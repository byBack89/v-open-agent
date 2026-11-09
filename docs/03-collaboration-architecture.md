# collaboration architecture - 다중 개발자 구현 경계

> 목적: 여러 개발자가 동시에 작업해도 판단 규칙, 계약, 보안 경계가 흐려지지 않도록 소유권과 의존 방향을 고정한다.

## 1. 문서 권한

| 문서 | 소유하는 결정 |
|---|---|
| `01-product-requirements.md` | 목표, 범위, REQ, 수용 기준 |
| `02-technical-specification.md` | 필드, enum, 상태, 전이, 시간 단위, 프로토콜, 보안 규칙 |
| `03-collaboration-architecture.md` | 모듈 경계, 허용 의존, 팀 소유권, 통합 순서 |
| `04-implementation-plan.md` | Task 순서, 선행 조건, 수용 테스트, 상태 |
| `adr/*.md` | 이미 내린 핵심 결정과 기각한 대안 |

코드가 문서와 다르면 코드에 맞춰 문서를 사후 수정하지 않는다. 구현 전에 상위 문서의 결정을 먼저 바꾸고, ADR이 필요한 변경은 같은 작업에서 기록한다.

## 2. 모듈 의존 방향

```text
contracts/                    language-neutral schemas and fixtures
  <- apps/server
  <- apps/android

apps/server/src/voa/contracts
  <- engine
  <- providers
  <- storage
  <- simulator
  <- server

engine.profile
  <- config

engine public API
  <- explain
  <- replay
  <- server

providers + config + engine + storage + explain
  <- server composition root

server JSON Schema
  <- simulator
  <- Android client
```

`apps/server`는 Docker 서버 Lane의 단일 소스 root이고 `apps/android`는 Android Lane의 단일 소스 root이다. Docker `server` target은 `apps/server/src`와 runtime config만 복사하고 `apps/android`, 서버 테스트, 개발 도구를 포함하지 않는다. `contracts`는 양쪽이 소비하는 중립 artifact root이다.

### 2.1 허용 규칙

- `contracts`: 다른 `voa` 패키지를 import하지 않는다.
- `engine`: `contracts` 및 `engine` 자신만 알며 I/O와 운영 런타임을 알지 못한다.
- `config`: 파일을 읽고 `engine.profile` 모델을 만드는 단일 경계다.
- `providers`: `ObservationDraft`만 생성하고 상태 판단을 하지 않는다.
- `explain`: `DecisionEngine` 공개 조회 API만 사용하고 private window를 읽지 않는다.
- `storage`: 메타데이터 영속화만 담당하고 엔진 전이를 유발하지 않는다.
- `server`: 인증, 시각, ID, queue, transport, persistence를 조립하는 composition root다.
- Android: 서버 JSON 계약의 consumer이며 판단 규칙을 복제하지 않는다.

### 2.2 금지 의존

- `engine -> server/config/storage/providers`
- `contracts -> engine/server`
- `providers -> engine.state_machine`
- `Android -> Python private 구현`
- 어느 모듈에서도 OCR, ASR, VLM 원문을 명령으로 승격하는 경로

## 3. 공용 계약

### 3.1 Python 계약

- Pydantic 모델과 JSON Schema 스냅샷이 공식 계약이다.
- 새 필드, enum, reason code는 `02-technical-specification.md` 수정과 contract 테스트 실패 확인 없이 추가하지 않는다.
- engine public API는 `02-technical-specification.md` §4.1에 있는 메서드만 공유 경계로 사용한다.

### 3.2 Transport 계약

- REST와 WebSocket 메시지는 `voa.contracts.messages` 스키마와 fixture를 공유한다.
- Python 시뮬레이터와 Android는 같은 positive/negative fixture suite를 사용한다.
- transport 변경은 server, simulator, Android owner가 동일 변경 세트에서 검토한다.

### 3.3 데이터 계약

- SQLite schema는 `02-technical-specification.md` §8.1에 열거된 컬럼만 허용한다.
- raw media, token, secret, OCR/STT 전문은 DB, 로그, crash artifact에 저장하지 않는다.
- migration이 필요하면 schema 변경 ADR과 rollback 계획을 먼저 작성한다.

## 4. 팀 소유권

| Lane | 기본 소유 | 공유 파일 변경 시 필요 검토 |
|---|---|---|
| Contract | `apps/server/src/voa/contracts`, `contracts/schemas`, `contracts/fixtures` | Engine, Server, Android |
| Engine | `apps/server/src/voa/engine`, `apps/server/tests/engine` | Contract, Explain |
| Provider/Replay | `apps/server/src/voa/providers`, `apps/server/src/voa/simulator`, `apps/server/src/voa/replay` | Contract, Engine |
| Explain/Storage | `apps/server/src/voa/explain`, `apps/server/src/voa/storage` | Engine, Server |
| Server | `apps/server/src/voa/server`, server tests, Compose runtime | Contract, Storage, Android |
| Android | `apps/android`, Android tests | Contract, Server |
| Verification | integration fixtures, privacy tests, release gate | 모든 Lane |

하나의 Task에는 한 명의 최종 owner를 둔다. 공유 파일인 `02-technical-specification.md`, `contracts`, `messages`, `04-implementation-plan.md`를 두 Lane이 동시에 편집하지 않는다. 필요하면 Contract owner가 계약 변경을 먼저 병합하고 consumer Lane이 그 위에서 업데이트한다.

팀 병렬 작업은 모든 현재 파일을 보존하는 baseline commit이 있고 작업 트리가 깨끗한 상태에서만 시작한다. 현재처럼 초기 파일이 미추적 상태이면 팀 리더가 baseline 범위와 commit 전략을 먼저 확정한다.

## 5. 병렬 개발 가능 구간

### Stage A

- TASK-04, TASK-05, TASK-15, TASK-15A는 소유 파일을 분리하면 병렬 가능하다.
- TASK-06 -> 07 -> 08 -> 09 -> 10은 순차 통합한다.
- TASK-10 후 TASK-11, TASK-12, TASK-14는 병렬 가능하고 TASK-13은 TASK-12 후에 통합한다.

### Stage B

- TASK-16 -> 17 -> 18은 transport 기반을 만드는 순차 구간이다.
- TASK-18 후 TASK-19와 TASK-21은 서로 다른 파일 owner로 병렬 가능하다.
- TASK-20은 TASK-19 후, TASK-22는 TASK-20과 TASK-21 후, TASK-23은 마지막에 통합한다.

### Android

- AND-00의 message contract을 Contract owner와 Server owner가 먼저 고정한다.
- AND-01 후 session/watchdog Lane과 output Lane은 interface가 고정되면 병렬 구현할 수 있다.
- Android E2E는 Server Task가 병합된 고정 commit을 기준으로 수행한다.

## 6. 계약 변경 절차

1. 변경하려는 REQ, INV, 상태 전이, consumer를 기록한다.
2. 바뀌는 결정과 기각한 대안을 ADR에 기록한다.
3. `02-technical-specification.md`와 schema snapshot을 먼저 바꾸고 contract 테스트의 예상 실패를 확인한다.
4. producer 구현과 consumer 어댑터를 별도 commit으로 만든다.
5. Python simulator, Android, server E2E가 같은 fixture를 통과한 뒤 계약 변경을 완료한다.

하위 호환성을 유지하지 않는 변경은 schema version을 올리고, 서버와 클라이언트의 전환 순서를 ADR에 적는다.

## 7. 통합 규칙

- 각 Task는 자신의 소유 파일만 수정하고 관계없는 포맷 변경을 하지 않는다.
- 공유 계약 변경 commit을 consumer 구현 commit과 분리한다.
- 합치기 전 `scripts/check.sh`와 해당 Lane 전용 테스트를 모두 실행한다.
- 통합 담당자는 스키마 스냅샷, fixture, PLAN 상태, ADR을 최종 확인한다.
- 실패한 테스트를 임시 비활성화하거나 unknown을 clear로 바꿔 통합하지 않는다.

## 8. ADR 필요 조건

아래 중 하나라도 바뀌면 ADR을 작성한다.

- public schema, API, WebSocket message
- 엔진 상태, 전이 순서, reason code
- 시간 기준, ID 생성, 인증, token 수명
- 저장 schema, retention, 프라이버시 범위
- 새 런타임 의존성 또는 라이선스 의무
- Android min SDK, target SDK, vendor SDK 경계

ADR 템플릿과 상태 규칙은 `docs/adr/00-index.md`를 따른다.
