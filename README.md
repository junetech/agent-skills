# Agent Skills

여러 AI 코딩 에이전트에서 공통으로 재사용할 수 있는 skill 저장소입니다.
현재는 Claude Code, Codex, Kilo 같은 도구에서 같은 skill을 심볼릭 링크로 연결해
한 곳에서 관리하는 용도를 목표로 합니다.

## 핵심 아이디어

- 도구별로 같은 skill을 중복 관리하지 않게 합니다.
- 검증한 워크플로우를 한 저장소에서 업데이트하고 재사용할 수 있습니다.
- 각 에이전트의 skill 디렉터리에는 링크만 두고 실제 내용은 이 저장소에서 관리합니다.

## 포함된 Skills

이 저장소에서 버전 관리되는 공개 skill은 현재 2개입니다.

대부분의 에이전트는 아래 두 경우에 skill을 선택합니다.

1. 사용자가 skill 이름을 직접 언급할 때
2. 요청 내용이 skill 설명과 명확하게 일치할 때

| Skill | 언제 불리나 | 예시 요청 | 하는 일 |
| --- | --- | --- | --- |
| `git-workflow` | staged changes 리뷰, diff 요약, 커밋 메시지 작성, 커밋 직전 점검이 필요할 때 | `staged changes 리뷰해줘`, `지금 diff 요약해줘`, `커밋 메시지 써줘` | `git diff --staged` 기준으로 변경 사항을 요약하고, 리스크를 짚고, Conventional Commits 형식의 메시지를 작성합니다. |
| `review-pr` | PR 리뷰, pre-landing review, base branch 기준의 위험 점검이 필요할 때 | `이 브랜치 PR 리뷰해줘`, `main 기준으로 pre-landing review 해줘`, `병합(merge) 전에 위험한 부분 찾아줘` | base branch 대비 diff를 분석해 SQL 안전성, race condition, LLM trust boundary, 문서 누락 같은 문제를 점검하고 가능한 항목은 직접 수정합니다. |

## 구조

```plaintext
agent-skills/
├── git-workflow/
│   └── SKILL.md
├── review-pr/
│   ├── SKILL.md
│   ├── checklist.md
│   └── design_checklist.md
└── .system/               # 로컬/도구 생성 영역, 버전 관리 제외
```

## 설치

설치는 보통 두 방식 중 하나로 합니다.

### 방법 1. Skill별로 개별 연결

가장 보수적인 방식입니다. 각 에이전트의 skill 디렉터리 안에서 필요한 skill만
개별 심볼릭 링크로 연결합니다.

#### macOS / Linux

```bash
ln -s /path/to/agent-skills/git-workflow ~/.codex/skills/git-workflow
ln -s /path/to/agent-skills/review-pr ~/.codex/skills/review-pr
```

#### PowerShell

```powershell
New-Item -ItemType SymbolicLink `
  -Path "$HOME\.codex\skills\git-workflow" `
  -Target "D:\path\to\agent-skills\git-workflow"

New-Item -ItemType SymbolicLink `
  -Path "$HOME\.codex\skills\review-pr" `
  -Target "D:\path\to\agent-skills\review-pr"
```

### 방법 2. Skill 폴더 전체를 이 저장소로 대치

이 저장소를 특정 도구의 canonical skill 디렉터리처럼 쓰고 싶다면, 아예 도구의
skill 폴더 자체를 이 저장소로 연결할 수도 있습니다.

이 방식은 skill별 링크를 여러 개 만들 필요가 없고, 저장소에 추가한 skill이 바로
해당 도구에 반영된다는 장점이 있습니다.

#### macOS / Linux

기존 skill 폴더가 있으면 먼저 백업한 뒤 연결하는 편이 안전합니다.

```bash
mv ~/.codex/skills ~/.codex/skills.backup
ln -s /path/to/agent-skills ~/.codex/skills
```

#### PowerShell

기존 skill 폴더가 있으면 먼저 이름을 바꿔 백업한 뒤 연결합니다.

```powershell
Move-Item "$HOME\.codex\skills" "$HOME\.codex\skills.backup"

New-Item -ItemType SymbolicLink `
  -Path "$HOME\.codex\skills" `
  -Target "D:\path\to\agent-skills"
```

도구마다 skill 디렉터리 위치는 다를 수 있으니, 링크를 만들 위치만 각 도구에 맞게 바꾸면 됩니다.

## 참고

- `.system/` 폴더는 로컬 환경이나 도구가 생성하는 보조 영역일 수 있습니다.
- 이 저장소의 공식 공개 skill은 `git-workflow`, `review-pr` 두 개를 기준으로 관리합니다.
- 전체 폴더 대치 방식을 쓰면 `.system/` 같은 도구 생성 폴더도 이 저장소 아래에 생길 수 있습니다.

## License

Apache License 2.0
