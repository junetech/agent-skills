# git-workflow Skill — 커밋 메시지 검사 스크립트 추가

> **⚠ 이 플랜은 [`20260710_check_commit_msg_spec.md`](20260710_check_commit_msg_spec.md)에 의해 대체되었다 — 역사적 보존.**
>
> 계보: 이 문서(shell 미러) → [`20260710_commit_checker_python_rewrite.md`](20260710_commit_checker_python_rewrite.md)(Python 이식, **이것도 대체됨**) → spec 문서(현행).
> 아래 본문 말미는 후속으로 rewrite 플랜을 지목하지만, 그 권위는 다시 spec 문서로 넘어갔다.
>
> **구현하지 말 것.** 여기 기술된 `check_commit_msg.sh` / `.ps1` 은 **끝내 커밋되지 않았고**
> `HEAD`에 존재한 적이 없다. 이 문서가 그 존재의 유일한 기록이다.
>
> 보존 가치는 B1–B8, 특히 다음 세 문장에 있다. spec 문서가 그대로 인용한다:
>
> - **"버그가 버그를 가렸다."** B8은 B7을 고친 뒤에야 드러났다.
> - **"패리티 검사는 한 번 하고 끝나는 게 아니라, 고칠 때마다 다시 돌려야 한다."**
> - **"엔진에 넘긴 처리는 exit code 계약을 지켜주지 않는다."** (B4·B6·B7·B8)
>
> 다만 이 문서가 **진단하지 못한 것**이 있다. B1–B8 여덟 건은 전부 인자 파싱·파일 I/O·로케일
> 배관에 있었고 도메인 규칙에는 하나도 없었다. 그래서 옳은 결론은 "미러를 없애라"가 아니라
> **"배관을 없애라"** 였다. 후속 rewrite 플랜은 미러만 없애고 배관을 Python으로 이식했다가
> 같은 실패 모드를 한 번 더 만들었다(spec 문서 「결함 2·5」).

## Goal

`git-workflow` 스킬에 Conventional Commits 타이틀 검사 스크립트(bash + PowerShell 미러)를 추가하고,
`SKILL.md`의 타이틀 검증 지시를 이 스크립트 호출로 교체한다.

두 가지 동기:

1. **정확성**: 현재 `SKILL.md`는 `echo -n "title" | wc -c` 로 49자 제한을 검증하라고 지시하는데,
   이건 **한글 타이틀을 바이트 수로 3배 과산정**하는 잘못된 방법이다(`wc -c` = byte count).
   두 스크립트는 Unicode East Asian Wide/Fullwidth 폭(2칸)을 제대로 세므로,
   SKILL.md의 규칙(≤49칸)과 검증이 드디어 일치한다.

2. **권한 요청 frictions 제거**: 여러 후보 타이틀의 글자 수를 셀 때마다 for-문 등
   인라인 스크립트를 실행하면 매번 권한 요청이 떠서 번거롭다. 스킬에 번들된 스크립트를
   호출하면 권한 요청 없이(또는 한 번의 승인으로) 반복 검증이 가능하다.
   `-t`/`-Title` 파라미터는 반복 가능하므로 후보 여러 개를 한 번에 검사할 수도 있다.

## 배경 — 왜 두 버전인가

세 호스트의 Windows 셸이 다르다:

| 호스트 | Windows 기본 셸 | `.sh` | `.ps1` |
| --- | --- | --- | --- |
| Claude Code | Git Bash (MINGW64) | 네이티브 | `pwsh -File` (pwsh 설치 시) |
| opencode | pwsh | `bash` 필요 (Git Bash 의존) | 네이티브 |
| Linux/macOS | bash/sh | 네이티브 | 해당 없음 |

두 스크립트는 서로 mirror(동일 CLI, 동일 출력, 동일 exit code)이므로,
스킬에 둘 다 두면 호스트별로 네이티브 실행 경로가 하나씩 보장된다.
로직 중복은 이미 발생한 비용이고, 스킬에 동봉하면 그 비용이 드러나 관리된다.

## Key changes

### 1. `git-workflow/scripts/check_commit_msg.sh` (신규)

사용자가 verbatim으로 제공한 bash 원본을 복사한 뒤, 실환경 검증에서 드러난 버그 2건을 수정했다(아래 "검증 중 발견한 버그" 참조).
파일은 LF 줄바꿈, 실행 비트 불필요(호스트가 `bash <path>`로 호출).

인터페이스 계약:

- `-t/--title "<title>"` (반복 가능): 타이틀 후보 검사(드래프트 리뷰)
- `-f/--file <path>` 또는 bare 인자: 커밋 메시지 파일 검사(commit-msg hook)
- 검사 항목: (1) 타이틀 ≤49 디스플레이 칼럼, (2) Conventional Commits prefix `<type>(<scope>)!: <summary>`, (3) 끝 마침표 금지, (4) 본문 있으면 타이틀과 빈 줄 사이
- 출력: `NNN  OK/FAIL  <title>` + FAIL 시 `- <reason>` 행들
- exit: 0 = 전부 통과, 1 = 위반, 2 = usage error
- 타입 허용 목록: `feat|fix|refactor|docs|perf|test|chore`

### 2. `git-workflow/scripts/check_commit_msg.ps1` (신규)

사용자가 verbatim으로 제공한 PowerShell 미러를 복사한 뒤, 훅 인자 바인딩 버그 1건을 수정했다(아래 참조).

인터페이스 계약: `.sh`와 동일(CLI, 출력, exit code). `-Title`/`-File` 파라미터명만 카멜케이스.
bare 위치 인자는 양쪽 모두 `-File`로 해석된다(commit-msg 훅이 넘기는 `$1`).
코드 포인트 폭 계산은 `[char]::ConvertToUtf32`로 서로게이트 페어를 묶어 emoji도 1회 카운트.

### 3. `git-workflow/SKILL.md` 수정

#### 3a. frontmatter `description` (3행) + `compatibility` (4행)

`description`은 스킬 트리거이자 사용자에게 노출되는 계약이다. 본문만 "display columns"로 고치고
frontmatter에 `≤49 chars`를 남겨두면 **이 스킬이 없애려던 바로 그 오해(바이트/문자 ≠ 칸)를 최상단에서 재생산**하게 된다.
그래서 본문과 함께 고쳤다. 271자로 `validate` 한도(1024)에 여유가 있다.

```md
description: ... Uses Conventional Commits format with a title width check (≤49 display columns, so CJK and emoji count as two).
```

`compatibility`는 opencode/PowerShell 검증 사실을 반영:

```md
compatibility: Tested on Claude Code with Git Bash (MINGW64) on Windows/Linux and opencode with PowerShell on Windows. Untested on macOS.
```

#### 3b. Title 검증 지시 (49–54행 근처)

현재:

```md
- ≤49 characters, hard limit (including the `<type>(<scope>): ` prefix)
  - Follows the 50-char title convention from [Tim Pope (2008)](...), with a 1-char safety margin so it never wraps in `git log --oneline`
  - Verify with `echo -n "title" | wc -c` (works in Git Bash / MINGW64)
- Use imperative mood ("fix", not "fixed")
- No trailing period
- Output `Title: XX characters ✓` after the draft; the user reads this line to confirm the limit was respected
```

변경:

```md
- ≤49 display columns, hard limit (including the `<type>(<scope>): ` prefix)
  - Follows the 50-char title convention from [Tim Pope (2008)](...), with a 1-char safety margin so it never wraps in `git log --oneline`
  - Why columns and not bytes/chars: `wc -c` counts bytes (triples a Korean title); `.Length` counts UTF-16 units (undercounts Hangul by half). East Asian Wide + Fullwidth code points occupy two columns, and are counted so.
  - Verify with the bundled checker (`scripts/check_commit_msg.{sh,ps1}`) — two mirrors of the same logic:
    - PowerShell: `& git-workflow/scripts/check_commit_msg.ps1 -Title '...'` (or `-Title 'a','b','c'` for multiple candidates at once)
    - bash: `bash git-workflow/scripts/check_commit_msg.sh -t '...'` (or `-t 'a' -t 'b' -t 'c'`)
    Pick whichever the current shell runs natively. Both print ` NNN  OK    <title>` and exit 0/1.
- Use imperative mood ("fix", not "fixed")
- No trailing period
- Output `Title: NN columns ✓` (NN = checker's column count) after the draft; the user reads this line to confirm the limit was respected
```

출력 계약 라인은 `characters` → `columns`로 용어 정정. 의미는 동일(사용자가 한 줄 읽고 제한 준수 확인).

#### 3c. "Title too long" 섹션 (82행 근처)

현재:

```txt
If the title exceeds 49 characters, provide 2–3 shorter alternatives with character counts. The count line is part of the output contract; without it the user cannot verify the limit was respected.
```

변경 — "characters" → "display columns", 그리고 검산은 체커로:

```txt
If the title exceeds 49 display columns, provide 2–3 shorter alternatives and run the checker on each to print column counts. The count line is part of the output contract; without it the user cannot verify the limit was respected.
```

## 검증 중 발견한 버그 (verbatim 원본에 있던 것)

계획은 두 스크립트를 "verbatim 복사, 로직 수정 없음"으로 가정했으나, 실제로 실행해보니 8건이 깨져 있었다.
여덟 다 **정적 리뷰로는 보이지 않고 실행해야만 드러나는** 종류였다.

버그가 버그를 가렸다는 점도 기록해둔다. B8(`.sh`가 인자를 조용히 버림)은 B7(`.ps1`이 `-x`에서 바인더 에러)을 고친 뒤,
같은 인자 모양을 양쪽에 먹여보고서야 드러났다. 패리티 검사는 **한 번 하고 끝나는 게 아니라, 고칠 때마다 다시 돌려야 한다.**

B2·B3·B4·B5·B7·B8은 모두 "두 스크립트는 미러다"라는 주장이 실제로는 성립하지 않던 지점이다.
미러 여부는 소스를 나란히 읽어서가 아니라, **같은 입력을 양쪽에 먹이고 stdout/stderr/exit code를 비교해야** 판정된다.
그리고 갈렸을 때 어느 쪽이 옳은지는 매번 따로 판단해야 한다 — B5는 `.ps1`이, B3는 `.sh`가 맞았다.

### B1. `.sh` — MSYS `grep -i`가 SIGABRT로 죽어 한글 폭 계산이 바이트로 퇴화 (Critical)

`select_utf8_locale()`이 `grep -qixF`로 `locale -a` 결과를 뒤졌는데, **Git Bash(MSYS2)의 grep은 `-i` 플래그에서 abort(rc=134)한다**.
`-qxF`는 정상, `-qiF`는 죽음 — `-i`가 원인.

결과: 시스템에 `C.utf8`이 **존재하는데도** 탐지에 실패 → `LC_ALL` 미설정 → `${#text}`가 문자가 아닌 **바이트**를 셈.
`feat(git-workflow): 커밋 메시지 컬럼 체커 추가`가 **57칸(실제 46칸)** 으로 나와, 이 스크립트의 존재 이유("바이트로 세지 말자")가 정확히 무너져 있었다.

수정: grep 대신 순수 bash 매칭. 후보들이 대소문자와 하이픈(`C.UTF-8` vs `C.utf8`)만 다르므로 `${var,,}`로 폴딩 후 `\n`-패딩 부분문자열 비교.

> 확인 사항: `LC_ALL`을 스크립트 중간에 `export`해도 bash는 로케일을 재초기화하므로 이후 `${#s}`가 문자 수를 센다.
> `printf -v cp '%d' "'$char"`도 UTF-8 로케일에서 코드포인트를 정확히 반환한다(`커` → 52964 = U+CEE4).

### B2. `.ps1` — 문서화된 훅 설치 형태가 모든 커밋을 거부 (Critical)

`.NOTES`가 `pwsh -NoProfile -File check_commit_msg.ps1 "$1"`을 안내하는데,
`-Title`이 `Position = 0`이라 git이 넘긴 **메시지 파일 경로가 `-Title`에 바인딩**된다 → 경로 문자열이 타이틀로 검사되어 항상 FAIL.

수정: 위치 인자를 `-File`로 옮겼다(`-Title`은 named 전용). bash의 `[[ -f $1 ]]` bare-arg 의미와 일치하게 되어 미러 주장이 비로소 성립.

### B3. `.sh` — 파일 모드가 CRLF의 `\r`를 벗기지 않음 (Warning)

`-f`로 CRLF 파일을 읽으면 줄 끝 `\r`가 남아:

- 빈 구분 줄이 non-empty로 잡혀 `body: line 2 must be blank` **오탐**
- 타이틀이 `title.\r`가 되어 `*.` 패턴을 빗나가 **끝 마침표 검사 누락**
- 폭이 1칸 과산정

수정: 읽기 루프에서 `line=${line%$'\r'}`. `.ps1`은 `Get-Content`가 알아서 처리하므로 영향 없었고, 이 지점이 두 스크립트가 실제로 갈라진 곳이었다.

### B4. `.ps1` — no-args가 usage가 아니라 PowerShell 바인딩 에러 (Warning)

`-Title`이 `Mandatory`라서 인자 없이 부르면 `.sh`의 `usage() → exit 2` 대신
`Cannot process command because of one or more missing mandatory parameters: Title.`이 ANSI 색코드째 튀어나오고,
**`$LASTEXITCODE`는 `2`도 아닌 빈 값**이 된다(네이티브 exit이 아니라 PS 엔진 에러이므로).
훅이나 CI가 exit code로 분기하면 usage error를 감지할 수 없다.

수정: 두 파라미터에서 `Mandatory` 제거 → no-args가 기본 파라미터 셋('Title')에 바인딩되도록 두고,
`Show-Usage`(stderr 2줄 + `exit 2`)를 추가해 dispatch에서 직접 잡는다. `-File ''` 같은 빈 값도 같은 경로로 떨어진다.

> `Mandatory`는 "값을 강제"하는 것처럼 보이지만, 실제로는 **에러 처리 권한을 PS 엔진에 넘기는** 선언이다.
> CLI 계약(exit code, stderr 형식)을 스크립트가 소유해야 하면 `Mandatory`를 쓰면 안 된다.

### B5. bare 인자로 없는 파일을 주면 두 스크립트의 진단이 갈림 (Warning)

`.sh`는 `[[ -f $1 ]] || usage`로 **usage**를 냈고, `.ps1`은 `-File`에 바인딩되어 **`no such file: <path>`** 를 냈다.
exit code는 양쪽 2로 같아 훅 동작엔 영향이 없었지만, 훅이 넘긴 경로가 잘못됐을 때 `.sh`는
"플래그를 잘못 줬다"고 말한다 — 실제 문제는 "파일이 없다"인데.

수정: `.sh`의 bare-arg 분기에서 존재 검사를 빼고 `check_file`에 맡겼다(`.ps1`이 더 옳았던 쪽).
대신 `-*) usage ;;` 분기를 앞에 추가해, 알 수 없는 **플래그**는 여전히 usage로 간다.
이게 없으면 `-x` 오타가 `no such file: -x`로 나온다.

### B6. `--help`가 exit 2 (Warning)

`.sh`의 `-h|--help`가 usage error와 같은 경로라 stderr + exit 2로 끝났다. help는 성공 경로이므로 stdout + exit 0이 관례다.
`.ps1`은 `-h`가 아예 없어 PowerShell 엔진의 `-?`가 처리했는데, **엔진 help는 `$LASTEXITCODE`를 설정하지 않는다** — B4와 정확히 같은 병.

수정: `usage()`에 exit code 인자를 받아 `0`이면 stdout, 아니면 stderr로 보낸다(`>&"$fd"`, MSYS에서 동작 확인).
`.ps1`에는 `-Help`(별칭 `-h`) 스위치를 직접 받아 `Show-Usage -ExitCode 0`으로 보낸다. `-?`는 여전히 엔진이 가져가지만, 우리가 소유한 `-h`는 계약을 지킨다.

> B4·B6·B7가 같은 뿌리다: **PS 엔진에 넘긴 처리(`Mandatory`, `-?`, unknown flag)는 exit code 계약을 지켜주지 않는다.**

### B7. `.ps1` — 알 수 없는 플래그가 PowerShell 바인딩 에러, `$LASTEXITCODE` unset (Warning)

`.sh`는 `-*) usage ;;` 분기로 알 수 없는 플래그를 usage(exit 2)로 잡는다.
`.ps1`은 `-x`를 주면 `A parameter cannot be found that matches parameter name 'x'`가 ANSI 색코드째 튀어나오고,
**`$LASTEXITCODE`가 unset**(빈 값)이 된다 — B4(Mandatory)·B6(엔진 `-?`)과 정확히 같은 병의 세 번째 발현.

수정: `param()`에 `[Parameter(ValueFromRemainingArguments)] [string[]]$Rest`를 두 파라미터 셋에 속하게 두고,
dispatch에서 `if ($Rest) { Show-Usage }`로 잡는다. `$Rest`는 ParameterSetName을 명시하지 않으면 양쪽 셋에 모두 속하지만,
bare positional은 `-File`의 `Position = 0`이 먼저 가져가므로 훅 동작은 회귀하지 않는다(바인딩 매트릭스로 검증).

부작용(개선): `-Title 'a' 'b'`처럼 쉼표를 빼먹은 호출이 지금은 조용히 `'b'`를 무시하던 게 usage로 떨어진다.
정상 배열 형태 `-Title 'a','b'`는 회귀 없음.

> **잔존(문서화됨)**: `-Title`/`-File`에 값을 안 주면 여전히 PS 바인딩 에러가 나고 `$LASTEXITCODE`가 unset된다.
> `$Rest`는 본문 진입 전 바인딩 단계에서 발생하는 이 에러를 잡지 못한다 — `param()` 방식의 구조적 한계다.
> bash는 `[[ ${2-} ]] || usage`로 exit 2를 낸다. 완전 패리티를 원하면 `param()` named 바인딩을 버리고 `$args`를
> bash처럼 수동 파싱해야 하지만(미러는 되나 dispatch 코드가 ~2배, PS 네이티브 파라미터 의미 상실), 훅은 항상
> `$1`을 넘기므로 현실 경로가 아니라고 판단해 **문서화된 잔존**으로 남긴다.

### B8. `.sh` — 인자를 조용히 버리고 검사를 건너뛴 뒤 exit 0 (Critical)

B7(`$Rest`)을 넣고 나서야 드러났다. `main()`이 `titles`와 `file`을 각각 채운 뒤 `if [[ -n $file ]]`로 파일을 우선하고,
같은 변수에 계속 덮어썼다. 그래서:

```sh
check_commit_msg.sh -t 'wip: BAD TITLE' /tmp/hook.txt   # 위반 타이틀이 통째로 무시됨 → exit 0
check_commit_msg.sh -f bad.txt -f hook.txt              # 첫 -f 가 버려짐          → exit 0
check_commit_msg.sh hook.txt hook.txt                   # 첫 경로가 버려짐          → exit 0
```

**검사기가 검사를 건너뛰고 OK를 내는 것**은 이 스크립트에서 가장 나쁜 실패 모드다.
훅은 인자가 하나뿐이라 안 터지지만, 에이전트가 `-t '<title>' COMMIT_EDITMSG`처럼 부르면 위반을 통과시킨다.

수정: `-f`/bare 분기에 `[[ -n $file ]] && usage`(두 번째 경로 거부), 루프 뒤에 모드 혼용 거부.

```sh
if [[ -n $file ]] && ((${#titles[@]} > 0)); then usage; fi
```

> `set -e` 주의: `[[ ... ]] && usage`를 단독 문장으로 쓰면 조건이 거짓일 때 AND-리스트가 non-zero를 반환한다.
> bash는 "실패한 명령이 `&&`/`||` 리스트의 일부이면 exit하지 않는다"는 예외를 적용하므로 case 분기 안에서는 안전하지만,
> 루프 뒤 검사는 의도를 분명히 하려고 `if`로 썼다.

이때 `.ps1`도 같은 규칙을 소유하도록 **파라미터 셋을 제거**했다. `-Title`/`-File` 상호배타를 파라미터 셋으로 표현하면
그 충돌을 바인더가 처리하고 — 스크립트 본문 실행 전에 던지므로 — `$LASTEXITCODE`가 unset이 된다(B4·B6·B7과 같은 뿌리).
셋 대신 dispatch에서 직접 검사한다. `-File`은 반복 경로를 **우리 에러로** 보고하려고 `[string[]]`로 바꿨다.

### 부수 문서 수정

- 두 헤더의 "conventions in **CLAUDE.md**" → 실제 규칙 소재인 `../SKILL.md`.
- 훅 설치 예시 경로 `scripts/...` → `git-workflow/scripts/...` (심링크 상대경로도 `../git-workflow/scripts/`로 정정).

## 파일 레이아웃 (결과)

```sh
git-workflow/
  SKILL.md
  scripts/
    check_commit_msg.sh    # bash 원본 (Claude Code/Git Bash, Linux/macOS 네이티브)
    check_commit_msg.ps1   # PowerShell 미러 (opencode/pwsh 네이티브)
```

`md-to-html/scripts/validate_output.py` 패턴과 일치. `.gitignore`는 `scripts/`를 막지 않음(확인 완료).

## Test plan

1. **PS 로컬 검증 (이 환경, build 단계에서 수행)**:
   - `pwsh -NoProfile -File git-workflow/scripts/check_commit_msg.ps1 -Title 'feat(scripts): add RESUME config validator'` → OK, exit 0
   - 한글 타이틀: `pwsh ... -Title 'feat(한글): 매우긴타이틀테스트입니다이것이'` → 칼럼 수가 UTF-16 .Length와 다르게 정산되는지 확인 (한글 1글자 = 2칸)
   - 초과 타이틀: 50칸 이상 → FAIL, exit 1, reason 출력
   - 잘못된 prefix: `update: foo` → FAIL (type 미허용)
   - 끝 마침표: `feat(x): do something.` → FAIL
   - `-File` 모드: 임시 파일로 title+빈줄+body / title+body(빈줄 없음) 두 케이스
   - usage error: 인자 없음 → exit 2
2. **bash 검증 (Claude Code = Git Bash/MINGW64에서 수행 완료)**: 동일 케이스를 `bash check_commit_msg.sh`로 돌려 PS와 출력/exit code 일치 확인.
   당초 "본 플랜 범위 밖, 사용자가 Linux에서 담당"으로 미뤘으나, Claude Code의 Bash 도구가 MSYS bash(`MINGW64_NT`)라 이 환경에서 바로 검증 가능했고 — 그 덕에 B1/B3이 잡혔다.
   미룬 검증이 곧 Critical 버그였다는 점이 이 플랜의 핵심 교훈.
3. **skills-ref validate**: `uv run --directory skills-ref skills-ref validate ../git-workflow/` — 통과(`Valid skill`).
4. **SKILL.md 워딩 검토**: `wc -c`가 **지시**로 남아있지 않은지 grep 확인. 남은 2건은 "왜 바이트 카운트가 틀린가"를 설명하는 근거 문장이므로 의도된 잔존.

### 최종 패리티 결과 (양쪽 stdout/stderr/exit code 동일)

| 케이스 | 폭 | 결과 | exit | 비고 |
| --- | --- | --- | --- | --- |
| `feat(git-workflow): add commit message column checker` | 53 | FAIL (>49) | 1 | |
| `feat(git-workflow): 커밋 메시지 컬럼 체커 추가` | 46 | OK | 0 | B1 |
| `fix(a): 🚀` (astral, 서로게이트 페어) | 10 | OK | 0 | |
| `wip: bad` | 8 | FAIL (type) | 1 | |
| `feat(a): title.` | 15 | FAIL (마침표) | 1 | |
| CRLF 파일, title + 빈 줄 + body | 10 | OK | 0 | B3 |
| LF 파일, 빈 줄 없이 body | 19 | FAIL (body) | 1 | |
| bare 인자 = 메시지 파일 (훅 형태) | — | OK | 0 | B2 |
| 인자 없음 | — | usage → stderr, stdout 비어 있음 | 2 | B4 |
| `-f ''` / `-File ''` | — | usage → stderr | 2 | |
| 없는 파일 (`-f`/`-File`, bare 인자 모두) | — | `no such file: <path>` → stderr | 2 | B5 |
| 알 수 없는 플래그 (`-x`) | — | usage → stderr | 2 | B7 |
| `-Title 'a' 'b'` (쉼표 누락) | — | usage → stderr | 2 | B7 부작용(개선). 배열 `-Title 'a','b'`는 회귀 없음 |
| `-h` / `--help` / `-Help` | — | usage → **stdout**, stderr 비어 있음 | **0** | B6 |
| 파일 경로 두 개 | — | usage (첫 경로를 버리지 않음) | 2 | B8 |
| 모드 혼용 (`-t`/`-Title` + 파일) | — | usage (타이틀을 건너뛰지 않음) | 2 | B8 |
| `-f`/`-File` 두 번 (플래그 반복) | — | `.sh`: usage / `.ps1`: 바인더 에러 | 2 / **unset** | 아래 "남은 차이점" |
| `-t`/`-Title` 두 번 (플래그 반복) | — | `.sh`: 정상 누적 / `.ps1`: 바인더 에러 | 0·1 / **unset** | 아래 "남은 차이점" |
| `-Title` / `-File` (값 누락) | — | `.sh`: usage / `.ps1`: 바인더 에러 | 2 / **unset** | 아래 "남은 차이점" |

exit code 열은 B4를 잡은 뒤 추가했다. 그전까지 패리티 표에 **exit code 열 자체가 없었고**, B4·B6·B7는 정확히 그 사각지대에 있었다.
표의 에러/help 경로 행들도 처음엔 없었고, 없는 동안 B5·B6·B8이 살아남았다.

## 결론 — 두 스크립트 접근이 끝내 해결하지 못한 것

> **이 플랜은 여기서 종료된다.** 후속: [`20260710_commit_checker_python_rewrite.md`](20260710_commit_checker_python_rewrite.md)
> — Python 단일 구현으로 전면 교체. 아래는 그 결정의 근거다.

B1–B8을 모두 고친 뒤에도 남은 것들. 이것들이 "미러 두 벌" 접근을 포기한 이유다.

### A. PowerShell 바인더 선점 — 회수 불가 (아래 1·3)

`$LASTEXITCODE`가 `2`도 `1`도 아닌 **unset**으로 남는다. B4·B6·B7·B8에서 네 번 같은 뿌리를 만났고
그때마다 소유권을 회수했지만, **반복 지정과 값 누락은 본문 실행 전에 거부되므로 회수할 방법이 없다.**
`[string[]]`로 바꿔도 소용없다. 스크립트가 exit code 계약을 온전히 소유할 수 없다는 뜻이다.

### B. "동일 CLI"는 처음부터 거짓이었다 (아래 2)

`.sh`의 `-t`는 반복 누적(`-t a -t b`)이 정상 사용법인데, `.ps1`의 `-Title`은 배열(`-Title a,b`)이 정상이고
반복하면 바인더 에러다. SKILL.md가 양쪽 문법을 **따로** 안내하는 것 자체가 미러가 아니라는 증거다.
헤더 주석의 `same CLI`는 끝까지 사실이 아니었다.

### C. 패리티는 수렴하지 않고, 고칠 때마다 다시 발산했다

B8은 B7을 고친 뒤에야 드러났다. **버그가 버그를 가렸다.** 미러가 둘인 한 검증 비용은
"한 번 맞추면 끝"이 아니라 "수정할 때마다 전 매트릭스 재실행"이다. 그리고 그 매트릭스는
자동화된 테스트가 아니라 **이 문서의 표**로만 존재한다 — 다음 수정자가 표를 안 돌리면 그대로 새는 구조다.

### D. wcwidth 테이블을 손으로 두 벌 유지해야 한다

`WIDE_RANGES`/`ZERO_RANGES` 30줄을 `.sh`와 `.ps1`에 각각 하드코딩했다. Unicode가 갱신되면 두 곳을
같이 고쳐야 하고, 어긋나도 아무도 모른다. 애초에 이 스크립트의 존재 이유가 폭 계산인데,
그 핵심 데이터가 이중화돼 있다.

### E. 이 접근과 무관하게 남는 Critical — 스킬 스크립트 경로

`SKILL.md`가 지시하는 호출이 **저장소 루트 기준 상대경로**다:

```sh
bash git-workflow/scripts/check_commit_msg.sh -t '...'   # cwd가 이 repo일 때만 동작
```

스킬은 `~/.claude/skills/git-workflow/`에 설치되어 로드된다. 다른 프로젝트에서 이 스킬을 쓰면
`No such file or directory` / `exit 127`이다. 이 저장소 안에서만 우연히 동작해왔다.
같은 줄 바로 위(52행)는 이미 `` (`scripts/check_commit_msg.{sh,ps1}`) `` 라는 올바른(스킬 디렉터리 기준) 표기를 쓰고 있어,
**한 문단 안에 두 규약이 섞여 있다.** `md-to-html/SKILL.md:159`의 `python md-to-html/scripts/validate_output.py`도 같은 패턴이다.

**이것은 shell/Python 선택과 무관하다.** 언어를 바꿔도 경로가 안 풀리면 똑같이 `exit 127`이고,
에이전트가 검산을 조용히 건너뛴다 — B8에서 고친 "검사기가 검사를 건너뛰고 OK를 낸다"와 같은 실패 모드다.
후속 플랜에서 **반드시 함께 처리해야 한다.**

### 원인별 상세 (A·B의 근거)

아래 셋은 모두 **PowerShell 바인더가 스크립트 본문 실행 전에 던지는** 경우다.
`exit`를 실행할 기회가 없으므로 `$LASTEXITCODE`가 `unset`으로 남는다(`2`도 `1`도 아님).
B4(`Mandatory`)·B6(엔진 `-?`)·B7(`-x`)·B8(파라미터 셋)에서 이미 네 번 나온 뿌리이고, 그때마다
"엔진에 넘긴 처리는 exit code 계약을 지켜주지 않는다"는 결론으로 우리가 소유권을 회수해왔다.
남은 셋은 **회수 방법이 없거나(1·3), CLI 설계 자체가 다른(2) 경우**다.

### 1. `-File a -File b` — 같은 named 파라미터 반복

`.sh`는 B8 수정으로 `usage`/exit 2. `.ps1`은 바인더가
`Cannot bind parameter because parameter 'File' is specified more than once.`를 던지고 unset.
`[string[]]`로 바꿔도 **반복 지정 자체를 바인더가 먼저 거부**한다(배열 문법 `-File a,b`는 우리가 잡아 exit 2).
결론: `.ps1`에서는 회수 불가. Python `argparse`에서는 `action='append'` + 개수 검사로 exit 2를 소유할 수 있다.

### 2. `-Title a -Title b` — 반복 가능성의 비대칭

`.sh`의 `-t`는 **반복 누적**이 정상 사용법(`-t 'a' -t 'b'` → 둘 다 검사, exit 0/1).
`.ps1`의 `-Title`은 배열(`-Title 'a','b'`)이 정상이고, 반복하면 위 1번과 같은 바인더 에러.
SKILL.md는 이미 양쪽 문법을 따로 안내하고 있으므로 **버그가 아니라 설계 차이**지만,
"동일 CLI"라는 헤더 주석과는 어긋난다. 결론: 미러를 유지하는 한 해소 불가.
Python 단일 구현에서는 `-t` 반복 누적 하나만 남으므로 비대칭 자체가 사라진다.

### 3. `-File` / `-Title` 값 누락

`.sh`는 `[[ ${2-} ]] || usage` → exit 2. `.ps1`은 `Missing an argument for parameter 'File'.` → unset.
1번과 같은 계열(바인더 선점). Python `argparse`는 값 누락에 exit 2를 보장한다(확인 완료).

> 셋 다 **훅 경로에는 영향이 없다** — 훅은 인자를 정확히 하나만 넘긴다.
> 영향 범위는 사람이나 에이전트가 손으로 잘못 호출했을 때의 진단 품질과 exit code뿐이다.
> 그럼에도 이 셋을 기록하는 이유는, **exit code 계약을 소유할 수 없는 구현은 계약을 지킨다고 말할 수 없기** 때문이다.

## 파일명 결정 (재논쟁 방지)

`validate_commit_title.{sh,ps1}`로 바꾸는 안을 검토했으나 **`check_commit_msg.{sh,ps1}` 유지**로 결정.
검사 4개 중 타이틀 검사는 3개(폭, prefix, 끝 마침표)이고, 네 번째 `body: line 2 must be blank`는 본문 검사다.
`-f` 모드는 메시지 파일 전체를 읽는 commit-msg 훅 경로다. `commit_title`은 실제보다 좁은 이름이 된다.
표의 마지막 행들(에러/help/잔존 경로) 역시 처음엔 없었고, 없는 동안 B5·B6·B7가 살아남았다.

## Assumptions

- ~~두 스크립트는 사용자가 verbatim 제공한 것을 그대로 복사한다(로직 수정 없음).~~
  → **깨졌다.** 실행해보니 Critical 2건 + Warning 5건(B3·B4·B5·B6·B7). verbatim 가정은 "실행해서 확인하기 전까지"만 유효하다.
- ~~`.sh` 검증은 사용자가 commit 이후 별도 수행 — 본 플랜은 Windows/pwsh 측만 검증.~~
  → **불필요한 유예였다.** Claude Code의 Bash 도구가 Git Bash라 같은 자리에서 검증된다.
- ~~PS 헤더의 경로 참조는 이미 유효하므로 수정 불필요.~~ → 헤더가 `CLAUDE.md`와 잘못된 `scripts/` 경로를 가리키고 있었다.
- `.sh`는 **MSYS bash에서도** 돌아야 한다(Claude Code의 Bash 도구). GNU/Linux bash와 동작이 같다고 가정하지 말 것 — `grep -i` abort가 그 반례.
- `SKILL.md` 본문은 한국어/영어 혼합 현행 유지(다른 스킬 컨벤션과 일치).
- 타입 허용 목록(`feat|fix|refactor|docs|perf|test|chore`)은 스크립트와 SKILL.md 35–42행이 이미 일치 — 변경 없음.
- `Title: NN columns ✓` 출력 계약은 준수. 에이전트가 체커를 실행해 칼럼 수를 얻거나, 체커 없이는 폭을 정확히 계산할 수 없으므로 체커 호출이 정규 경로.

## Risks

| 위험 | 완화 |
| --- | --- |
| 두 스크립트 간 미세한 동작 차이가 drift 발생 | **이미 현실화됨** (B2 훅 인자, B3 CRLF, B4 no-args, B7 unknown flag). 계약 명시와 헤더 주석만으로는 못 막았고, 양쪽을 같은 케이스로 **실행해 비교**해야만 잡혔다. 향후 로직 수정 시 위 패리티 표를 양쪽에 돌릴 것 — 성공 경로뿐 아니라 **usage/에러 경로의 exit code와 stderr까지** 비교할 것 |
| `-Title`/`-File` 값 누락이 PS에서 exit code unset 잔존 | `param()` 방식의 구조적 한계(본문 전 바인딩 에러, 스크립트 내 수정 불가). 훅은 항상 `$1`을 넘기므로 현실 경로 아님. 완전 패리티 원하면 `$args` 수동 파싱 전면 재작성(비용 과대) — **문서화된 잔존**으로 수용 |
| 한글/이모지 폭 로직이 호스트 로케일에 의존 | B1의 근본 원인. `.sh`는 UTF-8 로케일이 없으면 조용히 바이트를 센다. 현재는 경고를 stderr로 내지만, 경고를 못 보면 잘못된 숫자를 그대로 신뢰하게 됨 — 한글 타이틀 검사 결과가 40칸대 후반이면 한 번 의심할 것 |
| 호스트가 스킬 디렉터리를 복사/설치할 때 `scripts/`가 누락 | skills-ref validate는 파일 존재만 보고 누락을 잡지 못함. SKILL.md가 스크립트 경로를 명시하므로 번들 시 누락되면 에이전트가 경로를 못 찾아 즉시 실패 — 조용한 오작동 위험은 낮음 |
| `wc -c` 제거 후 구 에이전트 세션이 구 지시를 캐시 | 스킬은 로드 시점에 읽힘. 세션 재시작 시 새 SKILL.md 적용. 마이그레이션 이슈 아님 |
| PS 실행 정책(`ExecutionPolicy`)이 스크립트 블록 차단 | `-NoProfile -File` + 로컬 파일은 기본 `RemoteSigned`/`Bypass`에서 동작. hook 설치 시 `pwsh -NoProfile -ExecutionPolicy Bypass -File` 로 안내 가능(필요시 SKILL.md에 추가) |
