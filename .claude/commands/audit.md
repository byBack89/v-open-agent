---
description: "REQUIREMENTS/SPEC 기준 저장소 compliance audit (읽기 전용)"
argument-hint: "[범위 축소(선택), 예: engine]"
---

# Compliance audit (읽기 전용)

`docs/04-implementation-plan.md` §5.3 프롬프트를 수행한다. 범위: `$ARGUMENTS` (비어 있으면 전체)

1. `docs/01-product-requirements.md`의 우선순위 M REQ, `docs/02-technical-specification.md` §4.0 INV-01~10, `docs/03-collaboration-architecture.md`의 금지 의존을 체크리스트로 삼는다.
2. 각 항목을 코드와 테스트에서 근거(파일:줄)로 확인한다. 테스트를 실행할 수 있으면 `scripts/check.sh`도 실행한다.
3. 결과는 PASS / FAIL / UNVERIFIED로 표시한다. 확인하지 못한 것은 PASS로 쓰지 않는다.
4. 결함은 위험도순으로 정리한다. **코드는 수정하지 않는다.** 수정이 필요하면 새 Task를 제안한다.
