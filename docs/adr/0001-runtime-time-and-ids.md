# ADR-0001: 운영 시각과 ID 생성을 서버 경계에 둔다

- Status: accepted
- Date: 2026-11-09
- Owners: Engine, Server
- Related: ENG-14, ENG-17, INV-05, INV-06, TASK-05, TASK-16

## Context

엔진은 벽시계와 난수를 import할 수 없지만 운영 서버는 세션을 넘어 충돌하지 않는 ID와 UTC 시각이 필요하다.

## Decision

엔진은 `IdFactory`와 `UtcClock` Protocol만 소유한다. 테스트는 sequential/fixed 구현을 사용하고 운영은 `voa.server.runtime`의 `SecureIdFactory`와 `AnchoredUtcClock`을 주입한다.

## Alternatives

- 엔진에서 `time` 및 `secrets` 직접 사용: INV-06과 결정론을 깨므로 기각
- 세션별 sequential ID: 영속 DB의 primary key 충돌 가능성으로 기각

## Consequences

서버 runtime이 시각과 ID의 단일 composition owner가 된다. 엔진 테스트는 외부 환경에 의존하지 않는다.

## Verification

TASK-05의 결정론 테스트와 TASK-16의 runtime mapping/ID 형식 테스트로 강제한다.
