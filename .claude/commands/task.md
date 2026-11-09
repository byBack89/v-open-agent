---
description: "docs/04-implementation-plan.md 의 작업 단위(Task) 하나를 구현 — 인자 없으면 다음 TODO 자동 선택"
argument-hint: "[TASK-ID (예: TASK-07)] [추가 지시]"
---

# 작업 단위 하나 구현

대상: `$ARGUMENTS` (비어 있으면 `docs/04-implementation-plan.md`에서 선행 Task가 모두 DONE인 첫 TODO Task)

## 1. 읽기 (실제로 Read)
1. `docs/04-implementation-plan.md` — §1 진행 규칙, §5.1 공통 프롬프트, 대상 Task 행(REQ/산출물/수용 테스트/선행)
2. `docs/01-product-requirements.md` — 대상 Task의 REQ ID 행과 관련 T-R
3. `docs/02-technical-specification.md` — 대상 Task와 관련된 절. 판단 엔진 Task면 §4 전체(INV, 전이표, reason_code)
4. `docs/03-collaboration-architecture.md` — 대상 Task의 Lane, 허용 의존, 공유 파일 소유권
5. 선행 Task의 상태 확인. DONE이 아니거나 선행 산출물 코드가 없으면 **중단하고 보고**

## 2. 계획 보고
- 생성/수정할 파일
- REQ / INV / T-R ID
- 테스트 목록 (성공/실패/결측/지연 각 1개 이상, 수용 테스트 전부 포함)
- 명백하고 낮은 위험의 로컬 작업은 보고 후 계속한다.
- SPEC에 없는 선택이 구현 결과를 달리하면 선택지와 추천안을 보고하고 확인한다.

## 3. 구현
- 테스트를 먼저 작성해 실패를 확인하고 → 구현 → 통과시킨다.
- Task 범위만 다룬다. 이름/필드/상태/reason_code는 SPEC 그대로 쓴다.

## 4. 검증 / 기록
- `scripts/check.sh`를 실행하고 출력을 확인한다(TASK-01 이전에는 해당 Task에서 만든다).
- `docs/04-implementation-plan.md`의 대상 Task 상태를 `DONE`으로 바꾼다. 설계가 바뀌었으면 SPEC도 갱신한다.
- PLAN §5.4 템플릿으로 보고하고, 다음 Task 후보를 한 줄로 제시한다. 커밋은 `AGENTS.md`의 Task 하나, commit 하나 규칙과 Lore 트레일러를 따른다.
