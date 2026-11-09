# ADR-0003: Android 참조 클라이언트와 vendor 어댑터를 분리한다

- Status: accepted
- Date: 2026-11-09
- Owners: Android, Server
- Related: DEV-01~05, OQ-02, OQ-03, AND-01~09

## Context

스마트글래스 기종과 SDK가 확정되지 않았지만 Stage B 서버 계약을 실제 클라이언트에서 검증할 필요가 있다.

## Decision

표준 Android 에뮬레이터에서 합성 관측을 송신하는 참조 클라이언트를 먼저 만든다. 실제 camera, IMU, microphone, HUD, button은 각 단계의 계약과 기종이 확정된 뒤 adapter로 추가한다.

## Alternatives

- 첫부터 특정 글래스 SDK에 종속: 기종 미정과 vendor lock-in으로 기각
- Python 시뮬레이터만 사용: Android 생명주기, 권한, TTS, haptic, watchdog 결함을 못 찾아 기각

## Consequences

Android core는 vendor 타입을 알지 못하고 모든 device 기능을 adapter로 받는다. 실기기 확정 전에도 Stage B 계약을 E2E로 검증할 수 있다.

## Verification

AND-06 Android 에뮬레이터 E2E와 AND-09 vendor adapter 교체 테스트로 강제한다.
