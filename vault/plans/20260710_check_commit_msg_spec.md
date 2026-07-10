# check_commit_msg.py — 사양서 및 구현 계획

> 이 문서는 `check_commit_msg.py`의 사양서다. 원래 두 계획서(shell 미러, Python 이식)를 대체했으나,
> 둘 다 삭제되었다. 현재는 구현이 완료된 상태로, 이 문서가 설계 결정의 유일한 기록이다.

## Goal

`git-workflow` 스킬에, 에이전트가 커밋 타이틀 후보의 **디스플레이 폭을 세기 위해** 호출하는
Python 스크립트 하나를 둔다. 그 이상은 하지 않는다.

## 왜 다시 쓰는가 — 요구사항 자체의 결함

앞선 두 계획서는 8건의 버그(B1–B8)를 잡고도 계속 새 버그를 만들어냈다. 원인은 구현이 아니라
**요구사항**이었다. 네 가지가 코드 한 줄 쓰기 전에 이미 잘못돼 있었다.

### 결함 1 — "bash와 PowerShell 두 벌로, 서로 미러로"

DRY 위반. B1·B2·B4·B6·B7과 30줄짜리 wcwidth 테이블 이중화의 직접 원인.
두 번째 계획서가 이미 정확히 진단했다. 유일하게 잡힌 결함이다.

### 결함 2 — "-t/-f/bare-arg를 받는 CLI로" *(미진단)*

`check_commit_msg.sh` 235줄의 구성:

| 영역 | 줄 수 | B1–B8 중 |
| --- | --- | --- |
| 도메인 규칙 (`check_title`) | ~24 | **0건** |
| 폭 계산 (테이블 + 2개 함수) | ~50 | B1 (로케일 배관) |
| 인자 파싱 · usage · 파일 I/O | ~110 | **B2·B3·B4·B5·B6·B7·B8** |

**규칙 자체에는 버그가 단 하나도 없었다.** 여덟 건 전부 배관에 있었다.
따라서 올바른 수정은 "배관을 Python으로 이식"이 아니라 **"배관을 삭제"** 다.
두 번째 계획서는 8건 중 7건을 argparse에 넘겨 없앴지만, 없앨 수 있었던 건 배관 자체였다.

### 결함 3 — "그리고 commit-msg 훅으로도 쓸 수 있게" *(미진단, 능동적으로 해로움)*

아무도 요청하지 않았고, 한 번도 설치된 적 없으며, 설치됐다면 저장소를 망가뜨렸을 기능이다.

조사 결과(2026-07-10):

- `.githooks/` 디렉터리 없음. `git config core.hooksPath` 미설정.
- 저장소 전체에서 `hooksPath`/`commit-msg` 언급 **0건** — 두 스크립트 자기 헤더 주석 제외.
- `SKILL.md`는 훅을 단 한 번도 언급하지 않는다. 스킬이 필요로 하는 건 오직 `Title: NN columns ✓` 한 줄이다.

그리고 실측 — 이 저장소의 최근 20커밋을 그 훅에 통과시키면 **11/20만 통과**한다:

```text
✗ Merge pull request #1 from junetech/my_skill_creator   ← git이 자동 생성. `git merge`가 막힌다
✗ fix(skills-ref,spatial-html): tighten checks           ← 정규식이 쉼표를 거부 (결함 5)
✗ add reference of skills-ref
✗ Update git-workflow skill
✗ add python cache files to .gitignore
✗ add md-to-spatial-html skill
✗ add skill-creator skill
✗ feat(md-spatial-html): evals config & test fixtures    ← 51칸
✗ docs(readme): fix stale filename and ... (187칸)
```

`git revert`(`Revert "..."`), `git commit --fixup`(`fixup! ...`), `--squash` 도 전부 거부된다.
현재 스크립트에는 이 예외 처리가 **없다**. 즉 이 모드는 검증된 적이 없다.

이 모드 하나가 B3(CRLF)·B5(bare arg 진단)·B8 절반(모드 혼용, 두 번째 경로)과
`no such file`·`empty commit message`·`#` 주석 스트립 경로 전부를 끌고 들어왔다.

**→ 삭제한다.** 나중에 훅이 실제로 필요해지면 그때 별도 진입점으로 만든다.

### 결함 4 — "≤49 characters"가 "≤49 display columns"로 조용히 바뀜 *(미진단)*

원래 `SKILL.md`는 **characters**였고, 검증 지시가 `wc -c`(= **bytes**)였다. 이건 진짜 버그다.
최소 수정은 bytes → characters다. 그런데 계획서는 bytes → **columns** 로 건너뛰었다.
이건 *더 엄격한 다른 규칙*이다 — 한글 요약 예산이 약 30음절에서 약 15음절로 절반이 된다.
`wc -c`가 틀렸다는 (옳은) 논증에 편승해 들어왔을 뿐, 아무도 명시적으로 결정한 적이 없다.

**2026-07-10 사용자 확정: columns 유지.** 다만 다음을 사양에 명시한다.

- `git log --oneline`은 앞에 short-sha 8칸을 붙인다. 49칸 타이틀은 실제 57칸으로 렌더된다.
  80칸까지 23칸 여유가 있다 — **49는 계산으로 도출된 경계가 아니라 관례**다(Tim Pope, 2008).
  따라서 폭 계산의 ±1칸 오차는 실질적 위험이 아니다. 이 사실이 결함 5의 수용 근거다.
- East Asian **Ambiguous** 문자(`→ … ' ± °` 등, 할당된 코드포인트 중 138,739개)는
  터미널 로케일에 따라 1칸/2칸이다. `wcwidth` 관례대로 **1칸**으로 센다.
  즉 "display columns"는 결정적 수치가 아니라 **명시된 관례 하의 근사치**다.

---

## Python 재작성 계획서에 남아 있던 결함

두 번째 계획서도 같은 병에 걸려 있었다. **실행해서 확인하지 않은 주장**이 세 개 있었다.

### 결함 5 (Critical, 신규) — Python의 stdout은 UTF-8이 아니다

계획서의 핵심 전제:

> "B1 (locale width) → ✘ 발생 불가. Python 3 문자열은 코드 포인트 단위, locale 무관"

**계산**에 대해서는 참이고, **출력**에 대해서는 거짓이다. CPython 3.14의 `sys.stdout`은
로케일 인코딩을 쓴다(UTF-8 모드 기본값은 3.15부터). 이 머신에서 실측:

```console
$ python -c "import sys; print(sys.stdout.encoding)"
cp949                          # Git Bash와 PowerShell 양쪽 모두

$ python -c "print(' 10  OK    fix(a): 🚀')"
UnicodeEncodeError: 'cp949' codec can't encode character '\U0001f680'
exit=1                         # ← 계획서 테스트 표에 "OK, exit 0"으로 적힌 바로 그 행

$ python -c "print(' 46  OK    feat(x): 커밋 메시지 컬럼 체커 추가')"
 46  OK    feat(x): Ŀ�� �޽��� �÷� üĿ �߰�
exit=0                         # 폭 46은 맞지만, 사용자가 읽을 줄이 깨진다
```

**체커가 크래시하고 exit 1을 낸다.** 호출자는 exit 1을 "타이틀 규칙 위반"으로 읽는다.
B8("검사기가 검사를 건너뛰고 OK를 낸다")의 정확한 거울상이며, 더 나쁘다 — 없는 위반을 보고한다.

교훈은 앞 계획서가 B4·B6·B7에서 네 번 도달한 것과 **완전히 같다**:

> "엔진에 넘긴 처리는 계약을 지켜주지 않는다. 소유권을 회수하라."

앞 계획서는 그 교훈을 argparse 층에만 적용하고 한 층 아래(인코딩)를 보지 않았다.
여기서 엔진은 CPython의 로케일 유도 stdout 인코딩이다.

**수정**: 출력 전에 `sys.stdout.reconfigure(encoding="utf-8", errors="replace")`. 실측 확인됨.

### 결함 6 (Warning, 기존) — 도메인 규칙에도 버그가 하나 있었다

`\([a-z0-9._/-]+\)` 는 쉼표를 허용하지 않는다. 이 저장소 자신의 커밋
`fix(skills-ref,spatial-html): tighten checks` 가 거부된다.
Conventional Commits 사양은 스코프를 "괄호로 감싼 명사"로만 규정하고 문자 집합을 제한하지 않는다.

**수정**: `\([^()]+\)`.

### 결함 7 (문서) — 옳은 결론, 틀린 근거

계획서:

> "combining mark의 `east_asian_width`는 `'A'`이고 `'W'`가 아니다" → 그러므로 zero-width를 먼저 검사해야 한다

전제가 참이면 **순서는 상관없다**(`'A'`는 `('W','F')`에 없으므로 어차피 fall-through).
실제로 순서가 중요한 이유는 따로 있다 — **Mn/Me이면서 동시에 eaw W/F인 코드포인트가 7개 존재**한다:

```text
U+302A..302D  IDEOGRAPHIC {LEVEL,RISING,DEPARTING,ENTERING} TONE MARK
U+3099        COMBINING KATAKANA-HIRAGANA VOICED SOUND MARK      cat=Mn eaw=W
U+309A        COMBINING KATAKANA-HIRAGANA SEMI-VOICED SOUND MARK
U+16FE4       KHITAN SMALL SCRIPT FILLER
```

또한 계획서가 제안한 zero-width 판정 `category(ch) in ('Mn','Me')` + 명시적 ZW 집합은
`unicodedata.combining()`으로 대체할 수 없다 — 실측: `combining('ั')==0`(태국어 Mn),
`combining('️')==0`(VS16), `combining('‍')==0`(ZWJ).

**수정**: 판정은 `category(ch) in {"Mn","Me","Cf"}` 하나로 통일하고(명시 ZW 집합 불필요 —
ZWSP·ZWJ·BOM·방향 표시자가 모두 `Cf`), **zero-width를 먼저** 검사한다. 근거를 코드 주석에 남긴다.

---

## 사양 (Contract)

### CLI

```text
usage: check_commit_msg.py TITLE [TITLE ...]

positional arguments:
  TITLE       commit title to check (repeat for several candidates)

options:
  -h, --help  show this help message and exit
```

**모드는 하나다.** 플래그로 받는 입력은 없다. 따라서 모드 혼용도, 인자 유실도,
"어느 모드를 의도했는지 추측"도 **구조적으로 불가능**하다 (B8 소멸).

### 출력

성공/실패 각 타이틀당 한 줄. 실패 시 사유 줄이 뒤따른다.

```console
$ python check_commit_msg.py 'feat(git-workflow): 커밋 메시지 컬럼 체커 추가'
Title: 46 columns ✓  feat(git-workflow): 커밋 메시지 컬럼 체커 추가

$ python check_commit_msg.py 'feat(git-workflow): add commit message column checker' 'wip: bad.'
Title: 53 columns ✗  feat(git-workflow): add commit message column checker
  - title is 53 columns, limit 49
Title: 9 columns ✗  wip: bad.
  - no Conventional Commits prefix `<type>(<scope>)!: <summary>`; type must be one of: feat, fix, refactor, docs, perf, test, chore
  - title ends with a period
```

`Title: NN columns ✓` 는 `SKILL.md`의 출력 계약 문자열 **그대로**다.
에이전트는 이 줄을 그대로 옮겨 적는다 — 계약 문자열의 단일 소스는 체커다.

### exit code

| code | 의미 | 소유자 |
| --- | --- | --- |
| 0 | 모든 타이틀 통과 | 스크립트 |
| 1 | 하나 이상 위반 | 스크립트 |
| 2 | usage 오류 (인자 없음, 알 수 없는 플래그) | argparse |

`-h/--help` → stdout, exit 0. usage 오류 → stderr, exit 2. **실측 확인됨**(아래 Test plan).

### 검사 항목 (정확히 3개)

1. 디스플레이 폭 ≤ **49 columns**
2. Conventional Commits prefix: `^(feat|fix|refactor|docs|perf|test|chore)(\([^()]+\))?!?: \S`
3. 타이틀이 마침표로 끝나지 않을 것

명령형 어조는 기계적으로 판정할 수 없으므로 검사하지 않는다(현행 유지).

> **왜 3개뿐인가**: 스크립트는 **에이전트가 할 수 없는 일**만 한다 — 디스플레이 폭 세기.
> 2·3번은 그 김에 공짜(각 3줄)라 남긴다. "본문 앞 빈 줄" 검사는 파일 모드에서만 도달 가능했고,
> 코드 블록 안의 빈 줄은 에이전트가 눈으로 본다. 함께 삭제한다.

### 폭 계산

```python
_ZERO_WIDTH_CATEGORIES = frozenset({"Mn", "Me", "Cf"})

def display_width(text: str) -> int:
    width = 0
    for char in text:
        # Zero-width first: U+3099 and six others are both a nonspacing mark
        # and East Asian Wide, and the mark wins.
        if unicodedata.category(char) in _ZERO_WIDTH_CATEGORIES:
            continue
        width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return width
```

shell판의 `WIDE_RANGES`/`ZERO_RANGES` 하드코딩 60줄(×2 파일) → 6줄.
Unicode 테이블은 CPython이 유지한다(현재 unidata 16.0.0).

**정확도 — 실측(`✓` = 터미널 렌더링과 일치):**

| 입력 | 계산 | 터미널 | |
| --- | --- | --- | --- |
| `한글` | 4 | 4 | ✓ |
| `🚀` `✅` (eaw=W emoji) | 2 | 2 | ✓ |
| `🇰🇷` (regional indicator flag) | 2 | 2 | ✓ |
| `é` (e + combining acute) | 1 | 1 | ✓ |
| `→` (eaw=A) | 1 | 1 | ✓ (관례) |
| `❤` `⚠` (eaw=N, text-presentation emoji) | 1 | 2 | **✗ 1칸 과소** |
| `⚠️` (+ VS16) | 1 | 2 | **✗ 1칸 과소** |
| `👨‍👩‍👧` (ZWJ 시퀀스) | 6 | 2 | **✗ 4칸 과대** |

**이 셋은 고치지 않는다.** 정확히 고치려면 Unicode `Emoji_Presentation` 속성과
grapheme cluster 분할이 필요하고, 둘 다 stdlib에 없다. VS16만 특수 처리하면
`⚠️`는 맞고 `❤`·`👨‍👩‍👧`는 여전히 틀리는데, **부분 수정은 emoji를 지원한다는 착시**를 만든다.
49칸 한도에는 23칸 여유가 있고(결함 4), 이 규칙의 존재 이유는 한글 폭이다.

이 표는 **스크립트 헤더 docstring에만** 명시한다. `SKILL.md`에는 넣지 않는다 —
타이틀에 emoji를 쓰는 경우는 드물고(정규식이 선두 emoji를 이미 거부한다),
에이전트 컨텍스트에 상시 로드되는 문서에 넣을 값어치가 없다.
대신 `SKILL.md`는 emoji 폭을 **주장하지 않는다**(3a 참조).

### 인코딩

`main()` 첫 줄에서 `sys.stdout` / `sys.stderr`를 UTF-8로 고정한다(결함 5).

---

## 비목표 (Non-goals)

명시적으로 하지 **않는** 것. 나중에 "왜 없지?"를 재논쟁하지 않기 위해 기록한다.

- **commit-msg 훅 모드** — 결함 3. 필요해지면 별도 진입점으로. merge/revert/fixup/squash 예외 처리가 선결 조건이다.
- **stdin 입력, 파일 입력** — 호출자가 없다. YAGNI.
- **`-t/--title` 플래그** — 위치 인자로 충분하다. 플래그는 모드를 암시하고, 모드는 B8을 부른다.
  타이틀은 반드시 type 단어로 시작하므로 `-`로 시작할 수 없다. (그래도 필요하면 `--` 구분자.)
- **본문/빈 줄 검사** — 파일 모드에서만 도달 가능했다.
- **명령형 어조 검사** — 기계적으로 불가능.
- **완전한 wcwidth 구현** — 위 표의 3개 오차를 문서화하고 수용한다.
- **shell 미러** — 결함 1.

---

## Key changes

### 1. `git-workflow/scripts/check_commit_msg.py` (신규, stdlib only)

- 약 70줄. `argparse` + `unicodedata` + `re`.
- 헤더 docstring: 무엇을 검사하는지, 왜 columns인지, emoji 오차표, `../SKILL.md` 참조.
  **훅 설치 안내는 넣지 않는다**(결함 3).

### 2. shell 스크립트 2개 삭제

- `git-workflow/scripts/check_commit_msg.sh`
- `git-workflow/scripts/check_commit_msg.ps1`

두 파일은 현재 인덱스에 `A`(staged)로만 존재하고 HEAD에는 없다. 사용자가 편집기에서
변경분을 검토할 수 있도록 **워킹 트리에서만 삭제**한다(인덱스는 건드리지 않는다).
`git status`는 `AD`로 표시된다.

### 3. `git-workflow/SKILL.md`

#### 3a. frontmatter

`description`의 `so CJK and emoji count as two` 는 **거짓**이다 — `❤`·`⚠`(eaw=N)는 1칸으로 센다.
`description`은 스킬 트리거이자 사용자에게 노출되는 계약이므로, 지킬 수 없는 주장을 두면 안 된다.
`so each CJK character counts as two` 로 정정한다. emoji는 언급하지 않는다.

> 이건 앞 계획서가 `≤49 chars`를 고치며 남긴 흔적이다. 폭 근사치를 실측하기 전에 쓴 문장이라
> emoji까지 정확한 줄 알았다. **검증 전에 쓴 계약 문장**이 또 하나 있었던 셈이다.

`compatibility`는 **실행 검증 후에** 채운다. 앞 계획서의 최대 교훈이
"검증하지 않은 호환성 주장이 Critical 버그를 숨겼다"는 것이었다. 최종값:

```md
compatibility: Requires python 3.7+ on PATH; one Python implementation, no shell mirror. Verified on Python 3.14 under Claude Code with Git Bash and under opencode with PowerShell, both on Windows with a cp949 locale. Untested on macOS/Linux.
```

#### 3b. 타이틀 검증 지시 — **스킬 디렉터리 기준 경로로**

현재 지시는 저장소 루트 기준 상대경로다:

```sh
bash git-workflow/scripts/check_commit_msg.sh -t '...'   # cwd가 이 저장소일 때만 동작
```

스킬은 `~/.claude/skills/git-workflow/`에 설치된다. 다른 프로젝트에서 쓰면 `exit 127`이고,
**에이전트는 검산을 조용히 건너뛴다** — 결함 3·B8과 같은 실패 모드다.
언어를 바꿔도 경로가 안 풀리면 똑같이 깨지므로 이번에 함께 고친다.

```md
  - Verify with the bundled checker — pass every candidate at once:
    `python <skill-dir>/scripts/check_commit_msg.py '<title>' ['<title>' ...]`
    `<skill-dir>` is this skill's own directory, reported by the harness when the skill loads.
    Never a repo-relative path: the skill is installed outside the repo.
    If `python` is not on PATH, try `python3`.
    It prints `Title: NN columns ✓` (or `✗` plus reasons) and exits 0/1.
```

인터프리터는 `python`. 이 저장소의 기존 관례(`md-to-html/SKILL.md:159`)와 일치하고,
Windows에서 `python3`는 Python 미설치 시 Microsoft Store 스텁으로 잡힐 수 있다.
(이 머신은 `python`·`python3`·`py` 모두 실제 3.14.3 → 확인됨.)

#### 3c. "Title too long" 섹션

변경 없음.

---

## Test plan

`build` 단계에서 **전부 실행**한다. 표만 있고 실행하지 않아 B1이 살아남았다.

> **실행 결과 (2026-07-10)**: Git Bash 19/19, PowerShell 11/11, `skills-ref validate` 통과,
> 저장소 밖 경로 호출 통과. 하네스: `scratchpad/contract_test.sh`.
> PowerShell에서 `$LASTEXITCODE`가 `1`·`2`로 정확히 설정됨 — `.ps1`이 끝내 소유하지 못했던
> 계약(앞 계획서 「결론 A: 회수 불가」)을 Python이 양쪽 호스트에서 소유한다.

### 1. 계약 검증 — 두 호스트(Git Bash, PowerShell) 모두에서

| 케이스 | 폭 | stdout | stderr | exit |
| --- | --- | --- | --- | --- |
| `feat(git-workflow): 커밋 메시지 컬럼 체커 추가` | 46 | `✓` | — | 0 |
| `feat(git-workflow): add commit message column checker` | 53 | `✗` + 사유 | — | 1 |
| `fix(a): 🚀` **(결함 5 회귀 테스트)** | 10 | `✓` | — | 0 |
| `fix(skills-ref,spatial-html): tighten checks` **(결함 6 회귀)** | 44 | `✓` | — | 0 |
| `wip: bad` | 8 | `✗` (type) | — | 1 |
| `feat(a): title.` | 15 | `✗` (마침표) | — | 1 |
| `feat!: drop legacy endpoint` | 27 | `✓` | — | 0 |
| `fixup! feat(a): x` | — | `✗` (prefix) | — | 1 |
| 타이틀 3개 (2 pass, 1 fail) | — | 3줄 | — | 1 |
| 타이틀 3개 전부 pass | — | 3줄 | — | 0 |
| 인자 없음 | — | 비어 있음 | `error: the following arguments are required: TITLE` | 2 |
| 알 수 없는 플래그 `-x` (단독) | — | 비어 있음 | `error: the following arguments are required: TITLE` | 2 |
| 알 수 없는 플래그 `'feat(a): x' -x` | — | 비어 있음 | `error: unrecognized arguments: -x` | 2 |
| `-h` / `--help` | — | usage | 비어 있음 | **0** |
| 빈 문자열 `''` | 0 | `✗` (prefix) | — | 1 |
| `-- -x` (구분자로 타이틀 강제) | 2 | `✗` (prefix) | — | 1 |

> **`-x`의 사유 메시지는 위치에 따라 다르다.** 단독으로 주면 argparse가 `-x`를 알 수 없는
> *옵션*으로 소비하고, 남은 위치 인자가 없으므로 `required: TITLE` 로 보고한다.
> 타이틀 뒤에 붙이면 `unrecognized arguments: -x` 가 된다.
> **계약은 exit code(2)와 스트림(stderr)이지 메시지 문구가 아니다** — 문구는 Python 버전마다도
> 달라진다(부록 5-4 참조). 이 표는 관측된 문구를 기록할 뿐, 그것을 계약으로 승격하지 않는다.
>
> 빈 문자열 행 주의: shell판은 `-t ''`를 **usage/exit 2**로 처리했다. 빈 타이틀은 오용이 아니라
> **규칙 위반**이므로 exit 1이 옳다. 의도된 동작 변경.

### 2. 결함 5 회귀 — 인코딩

`python check_commit_msg.py 'fix(a): 🚀'` 가 두 호스트에서 `UnicodeEncodeError` 없이
`Title: 10 columns ✓` 를 내고 exit 0.
`sys.stdout.encoding == 'cp949'` 인 환경에서 돌아야 의미가 있다 — 이 머신이 그렇다.

### 3. 폭 정확도

위 "정확도" 표 8행을 그대로 assert. 오차 3건은 **오차인 채로** assert한다(문서와 코드 동기화).

### 4. 경로 검증 (3b)

저장소 밖 cwd에서 `SKILL.md`의 호출 형태를 그대로 실행 → `exit 127`이 아닐 것.
shell판은 이 검사를 통과한 적이 없다.

### 5. `skills-ref validate`

```sh
uv run --directory skills-ref skills-ref validate ../git-workflow/
```

### 6. `SKILL.md` grep

`wc -c`, `bash`, `pwsh`, `PowerShell`, `mirror`, `.sh`, `.ps1` 가 **호출 지시**에 남아있지 않을 것.
(`wc -c`는 "왜 바이트가 틀린가"를 설명하는 근거 문장으로만 잔존 허용.)

---

## Assumptions

앞 계획서와 달리, **각 항목에 검증 방법을 명시**한다. 검증하지 않은 가정이 B1을 숨겼다.

| 가정 | 검증 |
| --- | --- |
| `python`이 두 호스트의 PATH에 있다 | ✅ 실측: Git Bash·PowerShell 모두 3.14.3 |
| `sys.stdout.encoding`이 UTF-8이 아닐 수 있다 | ✅ 실측: 양쪽 `cp949` → 결함 5 |
| `reconfigure`가 이를 고친다 | ✅ 실측: emoji·한글 정상 출력, exit 0 |
| argparse가 no-args → stderr/exit 2 | ✅ 실측 (`nargs="+"`) |
| argparse가 `-h` → stdout/exit 0 | ✅ 실측 |
| argparse가 위치 인자를 유실하지 않는다 | ✅ 실측: `'a' 'b' 'c'` → 3개 모두 |
| `category(ch) in {Mn,Me,Cf}`가 옳은 zero-width 판정 | ✅ 실측: `combining()`은 태국어/VS16/ZWJ에 0 반환 |
| zero-width를 먼저 검사해야 한다 | ✅ 실측: Mn/Me ∩ (W\|F) = 7개 코드포인트 |
| 훅 인프라가 존재하지 않는다 | ✅ 실측: `.githooks` 없음, `core.hooksPath` 미설정, 언급 0건 |
| 정규식이 쉼표 스코프를 거부한다 | ✅ 실측: 저장소 자체 커밋이 FAIL |
| `.sh`/`.ps1`는 HEAD에 없다 | ✅ 실측: 인덱스에 `A`, `git cat-file -e HEAD:...` 실패 |
| 타입 목록은 `SKILL.md`가 단일 소스 | 코드에 7개 그대로. 변경 없음 |

## Risks

| 위험 | 완화 |
| --- | --- |
| `python`이 PATH에 없는 호스트 | `SKILL.md`에 `python3` 폴백 한 줄. 실패는 조용하지 않다(exit 127 + stderr) |
| emoji 폭 오차 3종 | 문서화 + assert. 49칸에 23칸 여유(결함 4). 한글은 정확함 |
| Ambiguous 문자를 1칸으로 셈 | `wcwidth` 관례. `SKILL.md`·헤더에 명시 |
| 에이전트가 체커를 돌리지 않고 숫자를 지어냄 | 구조적으로 못 막는다. 계약 문자열을 체커가 소유해 **그대로 붙여넣게** 만들어 표면을 줄인다 |
| `unicodedata` 테이블이 Python 버전따라 변함 | 의도된 동작. 한글은 Unicode 1.0부터 안정 |
| 스킬 배포 시 `scripts/` 누락 | `skills-ref validate`는 못 잡는다. 누락 시 `exit 127`로 큰 소리로 실패 |

## 이 문서가 남기는 규칙

1. **주장은 실행해서 확인한다.** B1(shell)과 결함 5(Python)는 둘 다 "당연히 맞다"고 여겨
   한 번도 돌려보지 않은 층에 있었다.
2. **엔진에 넘긴 처리는 계약을 지켜주지 않는다.** PowerShell 바인더, argparse, 그리고
   CPython의 stdout 인코딩. 계약을 소유하려면 모든 층에서 소유해야 한다.
3. **검사기가 검사를 건너뛰거나 없는 위반을 보고하는 경로를 남기지 않는다.** B8과 결함 5는
   같은 병의 양면이다.
4. **요청받지 않은 모드를 만들지 않는다.** 훅 모드는 버그의 절반을 만들고 가치는 0이었다.

---

## 부록 — Linux 검증 시 유념할 점

2026-07-10 검증은 **Windows에서만** 수행했다(Git Bash + PowerShell, Python 3.14, cp949).
`SKILL.md`의 `compatibility`는 그 사실만 주장한다: `Untested on macOS/Linux`.
Linux 검증이 끝나기 전에 그 문장을 고치지 말 것 — 이 문서의 규칙 1이다.

### ⚠ 먼저 확인할 것 — `python`이 python2일 수 있다 (Critical 후보)

현재 `SKILL.md:58`은 이렇게 안내한다:

> `python <skill-dir>/scripts/check_commit_msg.py ...` — If `python` is missing, use `python3`.

**Windows 관례를 그대로 옮긴 것이고, Linux에서는 순서가 거꾸로일 수 있다.**

| 배포판 | `python` | 결과 |
| --- | --- | --- |
| Debian/Ubuntu (기본) | 없음 | `command not found`, exit 127 — 큰 소리로 실패, 안전 |
| Ubuntu + `python-is-python3` | python3 | 정상 |
| CentOS 7 / RHEL 7, 구형 Amazon Linux | **python2** | **아래 참조** |

`python2`로 이 스크립트를 실행하면 `from __future__ import annotations`(35행)에서
컴파일 단계 SyntaxError가 나고, CPython은 **exit 1**로 죽는다.
그런데 이 스크립트의 계약에서 **exit 1 = "타이틀이 규칙을 위반했다"** 이다.

> 체커가 실행조차 못 하고서 위반을 보고한다. **결함 5와 정확히 같은 실패 모드**이고,
> 파일 안의 버전 가드로는 막을 수 없다 — SyntaxError는 어떤 코드보다 먼저, 컴파일 시점에 난다.

**검증 항목**: `python2` 존재 시 실제 exit code가 1인지 확인. 1이라면 `SKILL.md`를
`python3` 우선으로 뒤집는다(Windows에서 `python3`가 실제 Python 3.14.3으로 확인됐으므로 회귀 없음.
Python 미설치 Windows에서 `python3`는 Microsoft Store 스텁이라 exit 9009 — 조용하지 않다).

```sh
command -v python && python -c 'import sys; print(sys.version_info[0])'
command -v python3 && python3 -V
```

### 갈리지 **않는** 것 (Windows에서 이미 검증됨)

| 항목 | 근거 |
| --- | --- |
| 줄바꿈 | `.gitattributes`에 `* text=auto`. 저장소에 LF로 저장되어 Linux 체크아웃도 LF |
| 실행 권한 | shebang 없음, mode `100644`. `./check_commit_msg.py` 로 직접 실행하지 말 것 — 항상 `python3 <path>` |
| 로케일 폭 계산 | 코드 포인트 기반. `LC_ALL`과 무관 (B1은 shell 전용 병이었다) |
| 인자 유실·모드 혼용 | 모드가 하나뿐이라 구조적으로 불가능 |

### 갈릴 수 있는 것 — 확인 순서대로

1. **stdout 인코딩.** Linux에서 `LC_ALL=C`는 PEP 538/540이 UTF-8로 자동 강제하므로,
   `use_utf8()`가 **없었어도** 아마 안 터졌을 것이다. 결함 5가 Windows에서만 드러난 이유다.
   그러나 `PYTHONCOERCECLOCALE=0 LC_ALL=C` 나 `LC_ALL=en_US.ISO-8859-1` 는 여전히 위험하다.
   `use_utf8()`가 그 전부를 막는다 — Windows에서 `PYTHONIOENCODING=ascii`로 **OS 무관하게 검증됨**.
   Linux에서 재확인만 하면 된다.

2. **Python 버전 하한 3.7.** `sys.stdout.reconfigure`(3.7)와
   `from __future__ import annotations`(3.7)를 쓴다. 3.6 이하는 지원하지 않는다.

3. **`unicodedata.unidata_version`.** Windows는 16.0.0. 배포판 Python이 낮으면
   Unicode 테이블이 달라질 수 있다. 아래 폭 표 assert가 잡는다.
   한글은 Unicode 1.0부터, `U+1F680`의 East Asian Wide 지정은 Unicode 9.0(≈Python 3.6)부터 안정이다.

4. **argparse 에러 *문구*.** 버전마다 다르다(3.12에서 바뀜).
   **계약은 exit code와 어느 스트림으로 나가느냐지, 문구가 아니다.** 문구 diff를 실패로 판정하지 말 것.

5. **Ambiguous 문자 렌더링.** 터미널 로케일이 `ko_KR.UTF-8`/`ja_JP.UTF-8`이면
   `→ … ' ± °`가 2칸으로 렌더된다. 우리는 1칸으로 센다(wcwidth 관례).
   **버그가 아니라 문서화된 관례다.** 실패로 기록하지 말 것 — 결함 4 참조.

### 실행할 것 (복붙)

Windows 검증에 쓴 하네스는 scratchpad에 있었고 커밋되지 않았다. 아래가 그 등가물이다.
저장소 루트에서 실행한다.

```sh
PY=${PY:-python3}
S="$(git rev-parse --show-toplevel)/git-workflow/scripts/check_commit_msg.py"
pass=0; fail=0

t() {  # t <name> <want_exit> <needle|-> -- <argv...>
    local name=$1 want=$2 needle=$3; shift 3; shift   # drop the `--`
    local out rc
    out=$("$PY" "$S" "$@" 2>&1); rc=$?
    if [[ $rc == "$want" && ( $needle == - || $out == *"$needle"* ) ]]; then
        echo "  ok   $name"; pass=$((pass + 1))
    else
        echo "  FAIL $name (exit=$rc want=$want)"; echo "       ${out%%$'\n'*}"; fail=$((fail + 1))
    fi
}

echo "interpreter : $("$PY" -V 2>&1)"
echo "unidata     : $("$PY" -c 'import unicodedata; print(unicodedata.unidata_version)')"
echo "stdout enc  : $("$PY" -c 'import sys; print(sys.stdout.encoding)')"

t 'korean, 46 cols'      0 'Title: 46 columns ✓' -- 'feat(git-workflow): 커밋 메시지 컬럼 체커 추가'
t 'too long, 53 cols'    1 'limit 49'            -- 'feat(git-workflow): add commit message column checker'
t 'emoji (defect 5)'     0 'Title: 10 columns ✓' -- 'fix(a): 🚀'
t 'comma scope (def 6)'  0 'Title: 44 columns ✓' -- 'fix(skills-ref,spatial-html): tighten checks'
t 'bad type'             1 'no Conventional'     -- 'wip: bad'
t 'trailing period'      1 'ends with a period'  -- 'feat(a): title.'
t 'breaking, no scope'   0 'Title: 27 columns ✓' -- 'feat!: drop legacy endpoint'
t 'merge commit'         1 'no Conventional'     -- 'Merge pull request #1 from junetech/my_skill_creator'
t 'empty title'          1 'Title: 0 columns ✗'  -- ''
t '3 titles, 1 fails'    1 'Title: 8 columns ✗'  -- 'feat(a): x' 'wip: bad' 'fix(b): y'
t 'no args'              2 -                     --
t 'unknown flag -x'      2 -                     -- -x
t 'help'                 0 'usage:'              -- -h

# streams: -h is a success path, misuse is not
"$PY" "$S" -h >/tmp/o 2>/tmp/e; [[ -s /tmp/o && ! -s /tmp/e ]] \
    && { echo '  ok   -h  -> stdout only'; pass=$((pass+1)); } || { echo '  FAIL -h streams'; fail=$((fail+1)); }
"$PY" "$S"    >/tmp/o 2>/tmp/e; [[ ! -s /tmp/o && -s /tmp/e ]] \
    && { echo '  ok   no-args -> stderr only'; pass=$((pass+1)); } || { echo '  FAIL no-args streams'; fail=$((fail+1)); }

# hostile stdout encodings: each must print the rocket and exit 0 (defect 5)
for env in 'LC_ALL=C' 'LC_ALL=POSIX' 'PYTHONIOENCODING=ascii' 'PYTHONCOERCECLOCALE=0 LC_ALL=C'; do
    if out=$(env $env "$PY" "$S" 'fix(a): 🚀' 2>&1) && [[ $out == *🚀* ]]; then
        echo "  ok   $env"; pass=$((pass+1))
    else
        echo "  FAIL $env -> $out"; fail=$((fail+1))
    fi
done

# width table (catches a stale unidata_version)
"$PY" - "$S" <<'PYEOF'
import importlib.util, sys
spec = importlib.util.spec_from_file_location("c", sys.argv[1])
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
sys.stdout.reconfigure(encoding="utf-8")
cases = [("한글",4),("🚀",2),("✅",2),("🇰🇷",2),("é",1),("→",1),("Title: ",7),
         ("❤",1),("⚠",1),("⚠️",1),("👨‍👩‍👧",6)]   # last four are the documented approximations
bad = [(t, w, m.display_width(t)) for t, w in cases if m.display_width(t) != w]
for text, want, got in bad:
    print(f"       width({text!r}) = {got}, want {want}")
sys.exit(1 if bad else 0)
PYEOF
if [[ $? == 0 ]]; then
    echo '  ok   width table'; pass=$((pass+1))
else
    echo '  FAIL width table  <- check unidata_version above'; fail=$((fail+1))
fi

# the path must resolve from outside the repo (SKILL.md's <skill-dir> rule)
( cd /tmp && "$PY" "$S" 'feat(a): x' >/dev/null 2>&1 ) \
    && { echo '  ok   runs from outside the repo'; pass=$((pass+1)); } || { echo '  FAIL exit 127?'; fail=$((fail+1)); }

echo "======== $pass passed, $fail failed ========"
```

그리고:

```sh
uv run --directory skills-ref skills-ref validate ../git-workflow/   # uv 필요
```

### 통과하면 반영할 것

`git-workflow/SKILL.md` frontmatter의 `compatibility`에서 `Untested on macOS/Linux` 를
실제로 돌린 배포판·Python 버전으로 교체한다. **돌리지 않은 OS는 계속 `Untested`로 남긴다.**

Windows 기준선(비교용): Git Bash 19/19, PowerShell 11/11,
Python 3.14.3, unidata 16.0.0, 기본 `sys.stdout.encoding` = `cp949`.
