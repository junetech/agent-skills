# review-pr 안전성·호환성 개선 계획

## Goal

`review-pr` 스킬이 PR 또는 브랜치 검토 요청만으로 파일을 수정하지 않게 하고,
Claude Code 전용 기능이나 `origin/main` 가정 없이 Codex를 포함한 여러 에이전트 호스트와
로컬·원격 저장소 구성에서 일관되게 동작하도록 개선한다.

원래 요구사항은 Git으로 관리되지 않은 `TODO.md`의 `review-pr` 항목 여섯 개에
기록되어 있었다. 완료 조건은 이 여섯 항목을 모두 해결하고
`skills-ref validate ../review-pr/` 검증을 통과하는 것이다. 모든 항목이 완료된 뒤에는
남은 작업이 없으므로 `TODO.md`를 삭제한다.

## Key changes

### 1. 검토와 수정 권한 분리

- `review-pr/SKILL.md`의 설명과 워크플로를 기본 읽기 전용 검토로 바꾼다.
- 사용자가 `fix`, `apply`, `address`, `수정`, `고쳐`처럼 변경을 명시적으로 요청한 경우에만
  수정 모드로 진입한다.
- 검토 모드에서는 기계적인 문제도 수정하지 않고, 발견 사항과 권장 수정만 보고한다.
- 수정 모드에서도 커밋·푸시·PR 생성은 하지 않는다.

### 2. 호스트 중립 사용자 입력

- frontmatter의 Claude Code 전용 `AskUserQuestion` 도구와 호환성 문구를 제거한다.
- 판단이 필요한 수정은 호스트가 제공하는 사용자 입력 기능을 사용하고, 그런 기능이 없으면
  번호가 붙은 선택지를 일반 텍스트로 한 번에 제시한 뒤 응답을 기다리도록 한다.
- 질문을 할 수 없는 실행 환경에서는 판단이 필요한 항목을 건너뛰고 보고서에 남긴다.

### 3. 기준 브랜치와 비교 ref 판별 강화

- 현재 PR의 base(`gh pr view`)를 가장 먼저 사용하되 `gh`가 없거나 PR이 없어도 계속한다.
- 현재 브랜치의 upstream remote, `origin`, 단일 remote 순으로 사용할 remote를 찾는다.
- remote HEAD symbolic ref, remote 조회 결과, 로컬의 일반적인 기본 브랜치 ref 순으로 base를 찾는다.
- remote가 없거나 후보가 모호하면 `main`으로 추측하지 않고 사용자에게 base를 묻는다.
- 이후 명령은 브랜치 이름이 아니라 실제 존재하는 `<base-ref>`를 사용하며, fetch는 remote가 있을 때만 한다.

### 4. 검토 범위의 정확한 정의

- 커밋된 브랜치 변경: `git diff <base-ref>...HEAD`
- staged 변경: `git diff --cached`
- unstaged 변경: `git diff`
- untracked 파일: `git ls-files --others --exclude-standard`로 열거한 뒤 파일 내용을 직접 읽는다.
- 네 집합이 모두 비었을 때만 “Nothing to review”로 종료한다.
- 프런트엔드 판별과 문서 최신성 검사도 이 합집합의 변경 파일 목록을 사용한다.

### 5. finding 분류 일관성

- 모든 finding에 심각도(`CRITICAL`/`INFORMATIONAL`)와 처리 방식(`FIX`/`ASK`)을 부여한다.
- `POSSIBLE`은 세 번째 처리 방식이 아니라 낮은 신뢰도 표기이며 항상 `ASK`로 분류한다.
- 검토 모드는 `FIX`도 권장 수정으로만 출력하고, 수정 모드에서만 `FIX`를 자동 적용한다.
- `checklist.md`와 `design-checklist.md`의 용어와 출력 예시를 같은 모델로 맞춘다.

### 6. Codex 어댑터와 임시 TODO 정리

- `review-pr/agents/openai.yaml`에 `display_name`, `short_description`, 읽기 전용 기본 프롬프트를 추가한다.
- Git으로 관리되지 않은 `TODO.md`의 여섯 항목을 구현·검증한 뒤, 모두 완료된 내용만
  남은 파일을 삭제한다. 요구사항과 완료 근거는 이 계획서에 보존한다.

## Files and interfaces

- `review-pr/SKILL.md`: 트리거 설명, 모드 선택, base/ref 탐색, diff 수집, 결과 처리의 주 워크플로.
- `review-pr/checklist.md`: 공통 finding 분류와 검토/수정 모드별 출력 계약.
- `review-pr/design-checklist.md`: 디자인 finding을 동일한 `FIX`/`ASK` 체계에 매핑.
- `review-pr/agents/openai.yaml`: Codex UI 메타데이터. 아이콘이나 외부 도구 의존성은 선언하지 않는다.
- `TODO.md`: 최초 요구사항 입력으로만 사용한 비관리 임시 파일. 전 항목 완료 후 삭제.

## Test plan

1. 정적 검색으로 `AskUserQuestion`, “Fix-first, not read-only”, `fall back to main`,
   `includes both committed and uncommitted` 같은 기존 계약이 남지 않았는지 확인하고,
   완료된 임시 `TODO.md`가 남아 있지 않은지 확인한다.
2. 문서 워크스루로 다음 시나리오를 검증한다.
   - PR이 있고 `origin`이 있는 저장소
   - PR은 없지만 upstream 또는 remote HEAD가 있는 저장소
   - `origin` 없이 다른 이름의 remote만 있는 저장소
   - remote가 전혀 없고 로컬 기본 브랜치가 하나인 저장소
   - base 후보가 모호해 사용자 확인이 필요한 저장소
   - 커밋은 없고 untracked 파일만 있는 저장소
   - 검토 요청과 명시적 수정 요청
   - 낮은 신뢰도 디자인 finding
3. 저장소 루트에서 `uv run --directory skills-ref skills-ref validate ../review-pr/`를 실행한다.
4. `git diff --check`로 공백 오류를 확인하고 최종 diff를 읽어 문서 간 용어가 일치하는지 확인한다.

## Assumptions

- `git`은 필수다. `gh`와 remote 네트워크 접근은 선택 사항이며 실패해도 로컬 판별로 진행한다.
- base를 안전하게 판별할 수 없을 때 질문하는 것이 잘못된 `main` 비교보다 낫다.
- untracked 바이너리나 너무 큰 파일은 원문을 무리하게 출력하지 않고 파일 유형·크기를 확인한 뒤
  검토 가능한 방식으로 다루되, 검토 범위에서 조용히 제외하지 않는다.
- 사용자의 명시적 수정 요청은 발견된 문제의 수정만 허용하며 커밋·푸시 같은 배포 행위까지 허용하지 않는다.
