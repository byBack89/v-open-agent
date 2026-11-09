# architecture decision records

## 파일 이름

`NNNN-short-title.md`를 사용한다. 번호는 감소하지 않고 재사용하지 않는다.

## 상태

- `proposed`: 검토 중
- `accepted`: 구현 기준
- `superseded`: 더 최신 ADR로 대체됨
- `rejected`: 채택하지 않음

## 템플릿

```md
# ADR-NNNN: 제목

- Status: proposed
- Date: YYYY-MM-DD
- Owners: Contract, Engine, Server, Android 중 해당 Lane
- Related: REQ, INV, Task

## Context

결정이 필요한 사실과 제약

## Decision

채택한 규칙

## Alternatives

검토했지만 채택하지 않은 대안과 이유

## Consequences

장점, 비용, 후속 작업, 되돌림 방법

## Verification

이 결정을 강제하는 테스트와 운영 근거
```
