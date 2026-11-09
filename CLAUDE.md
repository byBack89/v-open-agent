# CLAUDE.md — Claude Code 작업 안내

공통 규칙은 `AGENTS.md`에 있다(Codex와 공용). 아래 import로 로드한다. **규칙은 `AGENTS.md`에서만 수정한다.** 이 파일에는 Claude Code 고유의 실행 방식만 적는다.

@AGENTS.md

---

## 1. 우선순위
사용자의 현재 지시 → `AGENTS.md` 규칙 → `docs/02-technical-specification.md` 및 `docs/03-collaboration-architecture.md` → 이 파일.
문서끼리 충돌하거나 명세에 없는 결정(라이브러리, 임계값, 필드)이 필요하면 **구현을 멈추고** 충돌 지점과 선택지를 제시한다.

## 2. 현재 상태
- TASK-01~03 완료, 다음 작업은 TASK-04다. 초기 작업은 아직 commit으로 나누어지지 않았다. 실행 환경은 Docker(§4)이고 진행 상황은 `docs/04-implementation-plan.md`의 상태 열이 기준이다.
- 실제로 파일을 만들고 명령을 실행하기 전에는 "테스트가 통과한다"고 말하지 않는다.

## 3. 슬래시 명령
| 명령 | 동작 |
|---|---|
| `/task` | `docs/04-implementation-plan.md`에서 선행 Task가 끝난 첫 TODO를 골라 구현 |
| `/task TASK-07` | 지정한 Task 구현 (선행 Task가 미완료면 중단) |
| `/audit` | 읽기 전용 compliance audit (PLAN §5.3) |

## 4. 환경과 검증 (Docker)
- **빌드/검사/서빙은 모두 도커 컨테이너 안에서 한다.** 소스는 호스트 폴더를 `/workspace`로 공유(bind mount)하고, 편집은 호스트에서 한다.
- 의존성은 이미지 안의 `/opt/venv`에만 설치한다. 호스트에 패키지를 설치하지 않는다(호스트 `.venv`는 쓰지 않음).
- 명령:
  ```bash
  scripts/build.sh                            # 서버 개발 이미지 수동 빌드
  scripts/dev.sh                             # 전체 검사 = 컨테이너에서 scripts/check.sh
  scripts/dev.sh pytest -q apps/server/tests/contracts  # 임의 명령
  docker compose --profile server up server  # 서버 실행 (TASK-16 이후), http://127.0.0.1:8765
  ```
- `dev` 서비스는 `network_mode: none`이다. 테스트는 네트워크 없이 통과해야 한다.
- 실모델 테스트는 `@pytest.mark.model`로 표시하고 기본 실행에서 제외한다.
- 실행하지 못한 검증은 `NOT TESTED` / `UNVERIFIED`로 보고한다.

## 5. Claude Code에서 특히 주의할 것
- `huggingface-cli download`, `hf download`, `wget`, 스크립트 안의 자동 `from_pretrained`를 쓰지 않는다(일부는 `.claude/settings.json`에서 차단).
- 엔진(`apps/server/src/voa/engine/`)에는 SaaS LLM이나 모델 호출을 넣지 않는다. INV-06 import 검사 테스트가 이를 강제한다.
- 테스트 fixture는 합성 JSON/JSONL만 쓴다. 음성/영상 파일은 만들거나 커밋하지 않는다.
- 커밋은 `AGENTS.md`의 Task 하나, commit 하나 규칙과 Lore 트레일러를 따른다. push는 사용자의 명시적 요청 없이 하지 않는다.

## 6. 서브에이전트
- 하나의 Task는 한 owner가 담당하고 여러 에이전트가 동시에 수정하지 않는다. 서로 독립적인 Task는 `docs/03-collaboration-architecture.md`의 Lane 소유권과 선행 순서에 따라 병렬 진행할 수 있다.
- `/audit`은 구현 결론에 고정되지 않은 독립 시각이 필요하므로 리뷰 에이전트에 맡겨도 된다.
