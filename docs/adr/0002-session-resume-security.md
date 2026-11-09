# ADR-0002: Resume token은 REST에서 회전하고 WebSocket은 access token으로 인증한다

- Status: accepted
- Date: 2026-11-09
- Owners: Server, Android
- Related: COM-01, COM-04, DEV-04, TASK-17, TASK-20, AND-02, AND-03

## Context

기존 계약은 WebSocket `auth` 후 resume token을 다시 제출하여 두 token의 역할과 만료 후 복구 규칙이 불분명했다.

## Decision

최초 세션 생성은 access token과 resume token을 발급한다. 재접속 시 REST resume endpoint가 두 token을 일회성으로 회전한다. 그 뒤 WebSocket을 새 access token으로 인증하고 `resume(last_alert_seq)`로 재전송 지점만 알린다.

## Alternatives

- WebSocket `auth` 후 resume token 재제출: 역할 중복과 만료 모호성으로 기각
- resume token을 회전하지 않음: 탈취 token 재사용 범위가 커져 기각
- 서버 재시작 후 세션 복원: 엔진 상태 비복원 규칙과 충돌해 MVP에서 기각

## Consequences

Android는 resume token을 Keystore key로 보호해야 한다. 서버 재시작 후 resume가 401이면 새 세션을 만든다. 이는 상태를 복원하지 않는 엔진 규칙과 일치한다.

## Verification

TASK-17에서 만료, 회전, 이전 token 재사용을 테스트하고 TASK-20과 AND-03에서 E2E resume를 검증한다.
