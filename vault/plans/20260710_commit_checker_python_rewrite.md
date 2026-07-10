# git-workflow Skill — 커밋 메시지 검사기 Python 재작성

> **⚠ 이 플랜은 [`20260710_check_commit_msg_spec.md`](20260710_check_commit_msg_spec.md)에 의해 대체되었다 — 역사적 보존.**
>
> 아래 본문은 스스로를 "forward-looking 후속"이라 부르지만, 그 권위는 spec 문서로 넘어갔다.
> **구현하지 말 것.** 실제 구현은 spec 문서를 따른다.
>
> 이 플랜이 놓친 것(spec 문서 「결함 2·3·5·6·7」):
>
> - shell 배관을 Python으로 **이식**하려 했다. B1–B8은 전부 배관에 있었고 규칙에는 없었으므로, 옳은 수정은 배관 **삭제**였다.
> - `-f`/훅 모드를 유지했다. 이 저장소에 훅 인프라는 존재한 적이 없고, 설치됐다면 `Merge pull request` 를 포함해 최근 20커밋 중 9개를 거부했을 것이다.
> - **"Python 3 문자열은 locale 무관"은 계산에만 참이고 출력에는 거짓이다.** 이 머신의 `sys.stdout.encoding`은 `cp949`이고, 아래 테스트 표에 "OK, exit 0"으로 적힌 `fix(a): 🚀` 행은 실제로 `UnicodeEncodeError` 로 죽으며 **exit 1**(= "규칙 위반")을 낸다.
> - 스코프 정규식이 쉼표를 거부해 이 저장소 자신의 `fix(skills-ref,spatial-html):` 커밋이 FAIL한다.
> - "zero-width를 먼저 검사하라"는 결론은 맞지만 근거가 틀렸다. 실제 이유는 Mn/Me이면서 동시에 eaw=W인 코드포인트가 7개(`U+3099` 등) 있기 때문이다.

## Goal

`git-workflow` 스킬의 커밋 메시지 검사기를 bash + PowerShell 미러 두 버전에서
**Python 단일 구현**으로 전면 교체한다.

동기: shell 미러는 B1–B8까지 8건의 실행-의존적 버그를 만들어냈다(아래 "배경" 인용).
미러를 유지하는 비용이 이득을 이미 초과했다. Python 단일 구현은 그 **버그 클래스
전체를 구조적으로 소멸**시킨다 — 인스턴스 8개를 고치는 게 아니라 발생기를 제거한다.

## 배경 — 왜 shell을 버리는가

`20260710_git_workflow_commit_msg_checker.md`에 기록된 8건의 버그 요약:

| # | 스크립트 | 증상 | 근본 원인 |
| --- | --- | --- | --- |
| B1 | `.sh` | 한글 폭이 바이트로 퇴화 (Critical) | MSYS `grep -i` SIGABRT → UTF-8 로케일 탐지 실패 |
| B2 | `.ps1` | 훅이 모든 커밋 거부 (Critical) | `-Title Position=0`에 파일 경로 바인딩 |
| B3 | `.sh` | CRLF `\r` 잔존 (Warning) | 파일 읽기 루프가 CR을 안 벗김 |
| B4 | `.ps1` | no-args가 binding error (Warning) | `Mandatory`가 PS 엔진에 에러 처리 위임 |
| B5 | `.sh` | bare arg 없는 파일 → usage (Warning) | `[[ -f $1 ]]`가 존재 검사를 usage로 회수 |
| B6 | 둘 | `--help`가 exit 2 / unset (Warning) | `.sh`는 usage와 같은 경로, `.ps1`은 엔진 `-?` |
| B7 | `.ps1` | unknown flag → binding error / unset (Warning) | PS 바인더가 처리, exit code 계약 파기 |
| B8 | `.sh` | 인자를 조용히 버리고 exit 0 (Critical) | `titles`/`file` 덮어쓰기 + 모드 혼용 허용 |

> "버그가 버그를 가렸다. B8은 B7을 고친 뒤 같은 인자 모양을 양쪽에 먹여보고서야
> 드러났다. 패리티 검사는 한 번 하고 끝나는 게 아니라, 고칠 때마다 다시 돌려야 한다."
> — 20260710 플랜

B1·B2·B3·B6·B7은 **플랫폼/엔진 의존** 버그(MSYS, PS 바인더). B5·B8은 **미러 drift** 버그.
Python 단일 구현은 두 클래스 모두 발생기 자체를 제거한다.

## Python 단일 구현이 구조적으로 소멸시키는 버그

아래 표의 ✘/△는 **실제로 Python 3.14.3에서 돌려 확인**했다. 추정이 아니다.

| 버그 | Python에서 발생 가능? | 이유 |
| --- | --- | --- |
| B1 (MSYS grep -i, locale width) | ✘ | Python 3 문자열은 코드 포인트 단위, locale 무관 |
| B2 (PS hook arg binding) | ✘ | argparse, 플랫폼 공통 |
| B3 (CRLF `\r` 잔존) | ✘ | `open(..., encoding='utf-8')` universal newlines |
| B4 (PS Mandatory binding error) | ✘ | argparse |
| B5 (bare arg 진단 갈림) | ✘ | 단일 구현 |
| B6 (엔진 `-?` no exit code) | ✘ | argparse `-h` → **stdout, exit 0** (확인) |
| B7 (unknown flag binding error) | ✘ | argparse unknown → **stderr, exit 2** (확인) |
| B8 (silent arg drop) | **△ 조건부** | **argparse 기본값이 B8을 그대로 재현한다.** 아래 참조 |

### ⚠ B8은 Python이 공짜로 해결해주지 않는다

"단일 구현이니 조용한 인자 유실은 없다"는 추론은 **틀렸다**. B8은 두 개의 별개 결함이었고,
그중 *조용한 덮어쓰기*는 미러 문제가 아니라 **인자 파싱 설계 문제**다. argparse 기본 동작으로 확인:

```python
p.add_argument('-t','--title', action='append')
p.add_argument('-f','--file')

p.parse_args(['-f','a.txt','-f','b.txt'])  # -> file='b.txt'   ← 첫 경로를 조용히 버림 (B8 재발)
p.parse_args(['-t','x','-f','a.txt'])      # -> title=['x'], file='a.txt'  ← 모드 혼용을 막지 않음
p.parse_args([])                           # -> exit 0 (!)     ← usage가 아님
```

따라서 Python 구현에서도 **명시적으로 세 가지를 검사해야 한다**:

1. `--file`을 `action='append'`로 받고 `len(files) > 1` → usage/exit 2 (`store`는 중복을 감지조차 못 한다)
2. `title`과 `file`이 동시에 채워지면 → usage/exit 2
3. 둘 다 비면 → usage/exit 2 (argparse는 아무것도 required가 아니면 exit 0으로 통과시킨다)

> B8의 교훈은 "미러를 없애라"가 아니라 **"검사기가 검사를 건너뛰고 OK를 내는 경로를 남기지 마라"** 였다.
> 언어를 바꿔도 그 교훈은 그대로 유효하다. Python이 소멸시키는 건 B1–B7이지 B8이 아니다.

### 소멸이 확인된 잔여 3건 (20260710 「결론」 A·B)

`.ps1` 바인더가 선점해 `$LASTEXITCODE`가 unset이던 세 경우는 argparse에서 모두 계약을 지킨다:

| 케이스 | `.ps1` | Python argparse |
| --- | --- | --- |
| `-f a -f b` (반복 지정) | unset (회수 불가) | `action='append'` + 개수 검사 → 2 |
| `-t a -t b` (반복 누적) | unset (설계 비대칭) | `action='append'` → 정상 누적 |
| `-f` (값 누락) | unset | **exit 2 (확인)** |

## Key changes

### 1. `git-workflow/scripts/check_commit_msg.py` (신규, stdlib only)

shebang `#!/usr/bin/env python3`. 실행: `python3 <skill-dir>/scripts/check_commit_msg.py ...`
(또는 `py -3` on Windows). **저장소 루트 기준 상대경로를 쓰지 말 것 — 3e 참조.**

**인터페이스 계약** (현재 shell 버전과 동일 — SKILL.md가 지시하는 호출 형태 그대로):

- `-t/--title "<title>"` (반복 가능): 타이틀 후보 검사
- `-f/--file <path>` 또는 bare 인자: 커밋 메시지 파일 검사
- `-h/--help`: usage → **stdout**, exit 0
- unknown flag / 값 누락 / 모드 혼용 / 두 번째 경로: argparse/명시 검사 → usage **stderr**, exit 2
- 검사 항목: (1) 타이틀 ≤49 디스플레이 칼럼, (2) Conventional Commits prefix, (3) 끝 마침표 금지, (4) 본문 전 빈 줄
- 출력: ` NNN  OK/FAIL  <title>` + FAIL 시 `          - <reason>` 행들
- exit: 0 = 전부 통과, 1 = 위반, 2 = usage error

**핵심 구현 결정**:

- **폭 계산**: `unicodedata.east_asian_width(ch) in ('W', 'F')` → 2칸. 현재 shell의
  WIDE_RANGES 30줄 하드코딩 → 1줄. Python 버전 업데이트 시 Unicode 최신판 자동 반영.
- **zero-width**: 작은 명시 set(`\u200b`–`\u200f`, `\ufeff`) + `unicodedata.category(ch) in ('Mn', 'Me')`
  (nonspacing / enclosing mark). shell의 ZERO_RANGES보다 넓지만 의도적 — combining mark는 폭 0이 맞다.
  - **검사 순서가 중요하다.** zero-width 판정을 `east_asian_width`보다 **먼저** 하지 않으면 1칸으로 샌다.
    확인 결과 combining mark의 `east_asian_width`는 `'A'`(ambiguous)이고 `'W'`가 아니며,
    ZWSP는 `'N'` + `category == 'Cf'`다. 폭 테이블만으로는 어느 쪽도 0칸이 되지 않는다.
  - `Mc`(spacing combining mark)는 폭이 있으므로 `startswith('M')`으로 뭉뚱그리면 안 된다. `Mn`/`Me`만 0칸.
- **서로게이트 페어링 불필요**: Python 3 문자열은 코드 포인트 단위. emoji 🚀는
  그냥 1문자(`len('🚀')==1`), `[char]::ConvertToUtf32` 같은 처리 없음.
- **universal newlines**: `open(path, encoding='utf-8')`가 CRLF/LF/CR을 `\n`로 정규화 — B3 소멸.
- **locale 무관**: 코드 포인트 기반 폭 계산, `LC_ALL`/`LANG` 탐지 불필요 — B1 소멸.
- **argparse 소유권**: `-h`, unknown flag, 값 누락 전부 argparse가 처리하고 exit code를 보장 — B4/B6/B7 소멸.
- **argparse 한계 보완**: argparse는 bare positional과 `-f`/`-t`를 자연스럽게 섞지 못하고,
  중복·혼용·no-args를 조용히 통과시킨다(위 「B8은 공짜로 해결되지 않는다」 참조). 따라서:
  - `--title`, `--file` **둘 다** `action='append'`. `--file`이 `store`면 `-f a -f b`의 중복을 감지조차 못 한다.
  - bare positional은 별도 `nargs='*'`로 받아 `--file` 목록과 합친 뒤, 합계가 2 이상이면 usage/exit 2.
  - `titles`와 `files`가 동시에 비어 있지 않으면(모드 혼용) usage/exit 2.
  - 둘 다 비면 usage/exit 2. argparse는 required가 없으면 no-args를 exit 0으로 통과시킨다(확인 완료).
  - B8의 교훈: "검사기가 검사를 건너뛰고 OK를 내는 것"이 가장 나쁜 실패.
- **타입 허용 목록**: `feat|fix|refactor|docs|perf|test|chore` (SKILL.md와 동일, 변경 없음).

### 2. shell 스크립트 2개 삭제

- `git-workflow/scripts/check_commit_msg.sh` — 삭제
- `git-workflow/scripts/check_commit_msg.ps1` — 삭제

단일 소스 진실(Single Source of Truth). 미러 주장을 유지할 필요 없음 — 미러가 없으니 drift도 없음.

> **git 상태 (2026-07-10 확인)**: shell 2개는 `A`(staged, 신규) 상태이며 **HEAD에는 없다**
> (`git cat-file -e HEAD:...` → 없음. 한 번도 커밋된 적 없음).
> 따라서 `Remove-Item`만으로는 부족하다 — 인덱스에 남는다. 다음 중 하나:
>
> ```sh
> git rm -f git-workflow/scripts/check_commit_msg.sh git-workflow/scripts/check_commit_msg.ps1
> ```
>
> 커밋되지 않았으므로 이력에는 아무 흔적도 남지 않는다. 20260710 플랜이 유일한 기록이 된다.
> — build 단계에서 `git status --short`로 다시 확인할 것.

### 3. `git-workflow/SKILL.md` 수정

#### 3a. frontmatter `compatibility` (4행)

현재 (20260710 수정본):
```
compatibility: Tested on Claude Code with Git Bash (MINGW64) on Windows/Linux and opencode with PowerShell on Windows. Untested on macOS.
```

변경:
```
compatibility: Requires python3 on PATH. Host-agnostic — single Python implementation, no shell mirror.
```

> `Tested on ...`은 **build 단계에서 실제로 돌린 뒤에** 채운다. 20260710 플랜의 최대 교훈이
> "검증하지 않은 호환성 주장이 Critical 버그를 숨겼다"는 것이었다(B1은 `.sh`를 한 번도 안 돌려봐서 살아남았다).

#### 3b. Title 검증 지시 (49–54행 근처)

현재 "two mirrors" 블록 전체를 Python 단일 호출로 교체.
**경로는 3e를 따른다** — `git-workflow/scripts/...`는 저장소 밖에서 풀리지 않는다:

```
- ≤49 display columns, hard limit (including the `<type>(<scope>): ` prefix)
  - Follows the 50-char title convention from [Tim Pope (2008)](...), with a 1-char safety margin so it never wraps in `git log --oneline`
  - Why columns and not bytes/chars: `wc -c` counts bytes (triples a Korean title); `.Length` counts UTF-16 units (undercounts Hangul by half). East Asian Wide + Fullwidth code points occupy two columns, and are counted so.
  - Verify with the bundled checker at `scripts/check_commit_msg.py` (relative to this skill's directory):
    - `python3 <skill-dir>/scripts/check_commit_msg.py -t '...'` (or `-t 'a' -t 'b' -t 'c'` for multiple candidates at once)
    - Prints ` NNN  OK    <title>` and exits 0/1. Works on all hosts with python3.
- Use imperative mood ("fix", not "fixed")
- No trailing period
- Output `Title: NN columns ✓` (NN = checker's column count) after the draft; the user reads this line to confirm the limit was respected
```

#### 3e. **[Critical] 스크립트 경로가 저장소 밖에서 풀리지 않는다**

언어 교체와 **무관하게** 반드시 함께 고쳐야 한다. 현재 SKILL.md의 호출 지시는 저장소 루트 기준 상대경로다:

```sh
bash git-workflow/scripts/check_commit_msg.sh -t '...'   # cwd가 이 repo일 때만 동작
```

스킬은 `~/.claude/skills/git-workflow/`에 설치되어 로드된다(확인 완료: 거기에 `scripts/`도 함께 복사돼 있다).
다른 프로젝트에서 이 스킬을 쓰면:

```
$ cd ~ && bash git-workflow/scripts/check_commit_msg.sh -t 'feat(a): x'
bash: git-workflow/scripts/check_commit_msg.sh: No such file or directory
exit=127
```

이 저장소 안에서만 우연히 동작해왔다. `exit 127`은 조용히 지나가기 쉬워서,
**에이전트가 검산을 건너뛰고 타이틀을 통과시킨다** — B8에서 고친 실패 모드와 동일하다.

`python3 git-workflow/scripts/check_commit_msg.py`로 그대로 옮기면 **같은 버그를 Python으로 이식**하게 된다.
(이 플랜의 초안 116행이 정확히 그랬다.)

수정 방향:

- 호출 지시를 **스킬 디렉터리 기준**으로 표기. 하네스가 매 호출 시 `Base directory for this skill: <path>`를 알려주므로
  에이전트가 절대경로를 조립할 수 있다.
- SKILL.md 52행이 이미 `` (`scripts/check_commit_msg.{sh,ps1}`) `` 라는 올바른 표기를 쓰고 있었다 —
  **한 문단 안에 두 규약이 섞여 있었다.** 하나로 통일한다.
- 같은 패턴이 `md-to-html/SKILL.md:159`(`python md-to-html/scripts/validate_output.py`)에도 있다.
  이 플랜 범위 밖이지만 **저장소 전반의 문제**로 별도 기록할 것.

"Why columns" 설명은 유지 — Python이 `unicodedata` 기반이라 더 정확하지만, 사용자가
왜 칼럼을 세는지 이해하는 건 여전히 가치 있다.

#### 3c. "Title too long" 섹션

변경 없음 (20260710 수정본 그대로 — "49 display columns", "run the checker").

#### 3d. "Output Structure" 행

변경 없음 (`Title: NN columns ✓`).

## 파일 레이아웃 (결과)

```
git-workflow/
  SKILL.md
  scripts/
    check_commit_msg.py    # Python 단일 구현 (stdlib only, 모든 호스트 공통)
```

`md-to-html/scripts/validate_output.py` 패턴과 일치. `.gitignore`는 `scripts/`를 막지 않음(확인 완료).

## Test plan

1. **Python 스크립트 로컬 검증** (build 단계에서 수행): 20260710 플랜의 패리티 표 16행
   전부를 Python 단일 구현으로 돌려 통과 확인. 특히:

   | 케이스 | 폭 | 결과 | exit |
   | --- | --- | --- | --- |
   | `feat(git-workflow): add commit message column checker` | 53 | FAIL (>49) | 1 |
   | `feat(git-workflow): 커밋 메시지 컬럼 체커 추가` | 46 | OK | 0 |
   | `fix(a): 🚀` (astral) | 10 | OK | 0 |
   | `wip: bad` | 8 | FAIL (type) | 1 |
   | `feat(a): title.` | 15 | FAIL (마침표) | 1 |
   | CRLF 파일, title + 빈 줄 + body | 10 | OK | 0 |
   | LF 파일, 빈 줄 없이 body | 19 | FAIL (body) | 1 |
   | bare 인자 = 메시지 파일 (훅 형태) | — | OK | 0 |
   | 인자 없음 | — | usage → stderr | 2 |
   | `-f ''` / 빈 경로 | — | usage → stderr | 2 |
   | 없는 파일 | — | `no such file: <path>` → stderr | 2 |
   | 알 수 없는 플래그 (`-x`) | — | usage → stderr | 2 |
   | `-t 'a' -t 'b'` (다중 타이틀) | — | OK × 2 | 0 |
   | `-t 'title' file.txt` (모드 혼용, B8) | — | usage → stderr | 2 |
   | `-f a -f b` (두 번째 경로, B8) | — | usage → stderr | 2 |
   | `file.txt file.txt` (bare 경로 두 개, B8) | — | usage → stderr | 2 |
   | `-f` (값 누락) | — | usage → stderr | 2 |
   | `-h` / `--help` | — | usage → stdout | 0 |

   > 아래 셋은 **argparse 기본값이 조용히 통과시키는** 케이스라 반드시 명시 검사해야 한다:
   > no-args(→argparse는 exit 0), `-f a -f b`(→마지막 값 채택), `-t x -f a`(→둘 다 채택).
   > 세 줄이 빠지면 B8이 Python에서 그대로 부활한다.

5. **경로 검증 (3e)**: 저장소 밖 cwd에서 SKILL.md의 호출 지시를 그대로 실행해 스크립트가 찾아지는지 확인.
   `cd ~ && <SKILL.md의 호출>` 이 `exit 127`이 아니어야 한다. shell 버전이 이 검사를 통과한 적이 없다.

2. **`unicodedata` 값 검증** (사전 확인 완료):
   - `east_asian_width('한')` == 'W' → 2칸 ✓
   - `east_asian_width('a')` == 'Na' → 1칸 ✓
   - `east_asian_width('🚀')` == 'W' → 2칸, `len('🚀')==1` → 총 2칸 (현재 shell과 일치) ✓
   - `category('\u0300')` == 'Mn' → 0칸 (combining mark) ✓
   - `'\u200b'` in zero-width set → 0칸 ✓
3. **skills-ref validate**: `uv run --directory skills-ref skills-ref validate ../git-workflow/` — 통과 확인.
4. **SKILL.md grep**: `wc -c`가 지시로 남아있지 않은지, `bash`/`pwsh`/`PowerShell`/`mirror`가
   호출 지시에 남아있지 않은지 확인.

## Assumptions

- **python3가 PATH에 있음**: 에이전트 컨텍스트는 사실상 보장(skills-ref가 동일 요구).
  훅 컨텍스트는 별개 — 훅은 옵션이라 설치 실패 시 큰 소리로 실패(silent skip이 아님).
  레포 선례: `md-to-html/scripts/validate_output.py`가 이미 stdlib-only Python 스킬 번들 패턴 확립.
- **현재 shell 버전은 별도 대화에서 커밋되지 않음**: 사용자가 "commit 안 하기로 했어"라고 했으므로,
  shell 파일 2개는 working tree에서 **삭제**만 하면 된다. staged 상태 처리는 build 단계에서 확인.
- **20260710 플랜은 shell 버전의 역사적 기록으로 보존**: B1–B8 교훈(특히 "버그가 버그를 가렸다",
  "패리티 검사는 고칠 때마다 다시 돌려야 한다")은 Python 재작성 플랜의 근거로 인용.
- **`unicodedata.east_asian_width`가 Python 버전을 따라감**: 구형 Python에서 최신 Unicode
  미반영 가능. 무시 가능 — Python 3.6+면 충분히 최신이며, 레포의 skills-ref 요구와 동일 기준.
- **argparse 에러 메시지가 Python 버전별 미세 차이**: 계약은 exit code/출력 형태(usage 2줄)라
  영향 없음. argparse 기본 메시지가 아닌 커스텀 usage를 쓰면 더 확실.
- 타입 허용 목록(`feat|fix|refactor|docs|perf|test|chore`)은 SKILL.md와 동일 — 변경 없음.
- `Title: NN columns ✓` 출력 계약 유지.

## Risks

| 위험 | 완화 |
| --- | --- |
| python3가 훅 컨텍스트의 PATH에 없음 | 훅은 옵션. 설치 실패 시 큰 소리로 실패(silent skip 아님). SKILL.md 에이전트 호출은 컨텍스트 보장 |
| `unicodedata`가 구형 Python에서 최신 Unicode 미반영 | Python 3.6+ 요구(skills-ref와 동일). 한글/이모지는 Unicode 1.0/6.0부터 안정 |
| argparse가 bare positional + `-f`/`-t` 혼합을 자연스럽게 안 함 | 명시적 검사 추가(모드 혼용 → exit 2). B8 교훈 반영 |
| Python 버전 올라도 `unicodedata` 테이블은 고정이 아님 | 의도된 동작 — Unicode 최신판 반영이 이득. shell 수동 테이블보다 나음 |
| shell 버전의 훅 설치 안내(`.githooks/`)가 Python으로 안 옮겨짐 | `.py` 헤더에 동등한 안내 추가. 단 **절대경로**로: `python3 /abs/path/to/check_commit_msg.py "$1"`. 훅은 임의의 저장소 루트에서 실행되므로 `git-workflow/scripts/...` 상대경로는 3e와 같은 이유로 깨진다 |

## Migration

- 20260710 플랜(`20260710_git_workflow_commit_msg_checker.md`)은 **shell 버전의 역사적 기록으로 보존**.
  이 플랜은 그 forward-looking 후속 — B1–B8 교훈이 Python 재작성의 근거.
- shell 파일 2개(`.sh`, `.ps1`)는 working tree에서 삭제. staged 상태 처리는 build 단계에서 확인.
- SKILL.md의 "two mirrors" / `bash` / `pwsh` / `PowerShell` 호출 지시 전부 Python 단일로 교체.
- `vault/plans/20260710_*.md`의 "Why two versions" 배경 섹션은 shell 버전 기록이므로 수정하지 않음
  (역사 보존). 이 플랜이 그 후속임을 명시.
