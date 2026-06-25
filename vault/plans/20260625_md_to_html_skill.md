# md-to-html Skill 계획 (md-to-spatial-html 후속)

## Goal

`md-to-spatial-html`을 흡수·확장한 후속 skill `md-to-html`을 만든다.
기존 skill은 "plan/spec/doc → 정적 spatial 문서" 한 가지 변환만 했지만,
참조 글([The Unreasonable Effectiveness of HTML](https://claude.com/blog/using-claude-code-the-unreasonable-effectiveness-of-html),
[html-effectiveness](https://github.com/ThariqS/html-effectiveness)) 이 주장하는 HTML의 진짜 강점은
**(1) 정보 밀도/공간성**, **(2) 상호작용성**, **(3) 사용자의 편집을 다시 Claude로 export 하는 양방향 루프** 다.
새 skill은 이 셋을 모두 담되, 단순 문서 변환의 안전성(self-contained, 원문 보존)은 잃지 않는다.

핵심 한 줄: **하나의 skill이 입력/요청의 성격을 보고 4개 모드 중 하나를 골라, 단일 파일 self-contained HTML 산출물을 원본 옆에 만든다.**

## 확정된 설계 결정 (사용자 확인 완료)

1. **관계 = 후속(successor)**: `md-to-html`이 단일 skill이 된다. `md-to-spatial-html`은 deprecate/제거하고,
   template·evals·validator를 이관한다. spatial 문서 변환은 새 skill의 **document 모드**로 그대로 살아남는다.
   (single source of truth — 두 skill의 trigger 충돌을 만들지 않는다.)
2. **상호작용 = opt-in**: 정적(no-JS)이 plan/spec 등의 **기본값**. vanilla JS는 source/요청이 요구할 때만 켠다.
   여전히 **single file, no CDN, no network**.
3. **지원 산출물 = 4종 전부**:
   - Richer static documents (catalog #03, #04, #06, #14, #16, #17)
   - Interactive editors (catalog #18, #19, #20)
   - Decks & explainers (catalog #09, #13, #15)
   - Design/prototype sandboxes (catalog #05, #07, #08, #10)

## Background — 소스에서 확인한 사실

참조 repo는 20개 self-contained HTML 예제 갤러리다. 구현자가 패턴을 그대로 참고할 수 있도록 카탈로그를 보존한다:

| # | 제목 | 분류 | 핵심 기법 |
| --- | --- | --- | --- |
| 01 | Three code approaches | Exploration | trade-off 주석 달린 side-by-side 비교 |
| 02 | Visual design directions | Exploration | 라이브 렌더된 레이아웃/팔레트 옵션 |
| 03 | Implementation plan | Planning | 타임라인 + data-flow 다이어그램 + mockup + risk table |
| 04 | Annotated PR | Code review | margin note 달린 diff, severity 태그, jump link |
| 05 | PR writeup | Code review | before/after 서술 + file-by-file 투어 |
| 06 | Module map | Code review | box-and-arrow + critical path 강조 |
| 07 | Living design system | Design | 인터랙티브 color swatch / spacing token |
| 08 | Component variants | Design | 모든 상태를 보여주는 contact sheet |
| 09 | Animation sandbox | Prototype | duration/easing **슬라이더** |
| 10 | Clickable flow | Prototype | 링크된 4개 화면 |
| 11 | SVG figure sheet | Illustration | 인라인 벡터 그림 |
| 12 | Annotated flowchart | Diagram | 클릭 가능한 step + timing |
| 13 | Arrow-key slide deck | Deck | 빌드 없이 **키보드 네비** 프레젠테이션 |
| 14 | How a feature works | Research | collapsible + **tabbed code** + FAQ + TL;DR |
| 15 | Concept explainer | Research | 인터랙티브 시각화 + glossary |
| 16 | Weekly status | Report | 차트 포함 요약 |
| 17 | Incident timeline | Report | 분 단위 post-mortem + 로그 발췌 |
| 18 | Ticket triage board | Editor | 컬럼 간 **draggable card** + markdown export |
| 19 | Feature flag editor | Editor | 의존성 경고 달린 **toggle** + diff copy |
| 20 | Prompt tuner | Editor | 변수 슬롯 편집 → **라이브 재렌더** |

글이 강조하는 원칙: zero-friction(브라우저 더블클릭), self-contained(파일 1개), 양방향(편집→export→Claude), 목적특화 일회용 UI, archival longevity.

## 1. Skill 아키텍처 — Mode Router (가장 중요한 신규 부분)

기존 skill은 단일 transform이라 router가 필요 없었다. 새 skill은 4개 산출물 family가 규칙이 서로 달라서,
**맨 앞에 모드 결정 규칙**을 둔다. 기본은 항상 **document 모드**이고, interactive로 가려면 명시적 신호가 있어야 한다(over-fire 방지).

| 신호 (source/요청) | 모드 | JS |
| --- | --- | --- |
| plan / spec / design doc / RFC / postmortem / review / "이거 HTML로", "render this" | **document** (기본) | 없음 (정적) |
| "triage board / kanban / 우선순위 보드", "toggle/flag editor", "prompt tuner", 편집·재배열·export 가 목적 | **editor** | opt-in |
| "slide deck / 발표자료 / deck", "concept explainer", 순차 제시·교육 | **deck** | opt-in (네비/토글 한정) |
| "animation sandbox / 파라미터 튜닝", "design system / swatches", "component variants", 값 조절→미리보기 | **sandbox** | opt-in |

라우팅 규칙 문장(SKILL.md에 명시):
- 애매하면 **document**. interactive 모드는 "사용자가 *도구*를 원한다"가 분명할 때만.
- 한 요청이 두 모드를 요구하면(예: 계획 문서 + 트리아지 보드) **각각 별도 파일**로 만들고 sidebar/peer link로 연결한다. 한 파일에 섞지 않는다.

## 2. Non-negotiable invariants (기존 7개 계승 + 신규 3개)

계승(기존 SKILL.md 규칙):
1. **`.md`를 보존한다** (source of truth). 같은 basename `.html`을 같은 디렉터리에 쓴다. 절대 덮어쓰지/지우지 않는다.
2. **단일 self-contained 파일.** CSS는 `<style>` 인라인, SVG 인라인, JS는 `<script>` 인라인. **CDN/외부폰트/네트워크 금지.** 더블클릭으로 오프라인 동작.
3. **document 모드는 content loss 0.** 모든 문단/코드/표/리스트가 escaped HTML로 살아남는다.
4. **peer link** — 관련 파일 묶음 변환 시 sidebar에서 형제 문서를 링크.
5. **footer attribution** — 매 파일 끝 `Source: <path>.md (markdown remains authoritative; this HTML is a view).`
6. **markdown-origin text는 HTML escape** (`&`/`<`/`>`/속성 따옴표; 코드는 `<code>` 안에서 escape).
7. **file/module/architecture 섹션 → inline SVG module map** (`<figure class="modmap">`) + 원문 보존. 스타일 리스트나 파일명 `<table>`로 대체 금지.

신규(JS 허용에 따라 추가):
8. **Progressive enhancement.** JS는 점진적 향상이어야 한다 — JS가 꺼져도 핵심 콘텐츠가 보여야 한다.
   deck은 슬라이드가 세로로 쌓여 보이고, editor/board는 데이터가 정적 리스트로 보인다. **JS 없으면 빈 화면 = 실패.**
   즉 콘텐츠는 실제 DOM에 있어야 하고, JS가 `innerHTML`로 처음부터 생성하면 안 된다.
9. **No network / no exfiltration.** `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`, `navigator.sendBeacon`,
   URL `import()`, 원격 `src/href`, `@import url(http…)` **전부 금지.** export는 **clipboard 쓰기 또는 로컬 파일 download만.**
10. **No XSS via echoed text.** 사용자/markdown 텍스트를 DOM에 넣을 때 `textContent`/escape 사용. 사용자 데이터에 `innerHTML` 사용 금지.

## 3. Per-mode playbook

### 3a. Document 모드 (기본, 정적) — 기존 skill을 그대로 + 레벨업
- 기존 SKILL.md의 **transform table 전체를 계승**(가장 가치 있는 부분): region band SVG, comparison card, scenario matrix, risk card, decision strip, modmap, pipeline, glossary, TL;DR 등.
- 레벨업 추가 컴포넌트(정적으로 구현, JS 불필요):
  - **Tabbed code/content**: `:target` 또는 `<details>` 기반 (catalog #14). JS 없이 라디오/`:target` CSS 토글.
  - **Annotated diff**: `<pre>` + 좌측 margin gutter + severity 색상 (catalog #04). 추가/삭제 라인 배경색.
  - **Inline-SVG chart**: 막대/스파크라인 등은 **소스에 데이터가 있을 때만** inline `<svg>`로. 차트 라이브러리 금지(self-contained).
  - **Timeline**: 사건 분 단위 세로 타임라인 (catalog #17).
- 규칙: 원문 보존 + escape + sidebar TOC + footer. (기존과 동일한 엄격함)

### 3b. Editor 모드 (opt-in JS) — 목적특화 편집기 + export 루프
정의적 특징: **사용자의 편집을 다시 Claude로 가져갈 수 있어야 한다.** export 없는 editor는 실패다.
- 참조 3종을 reference 컴포넌트로 제공: triage board(#18, draggable card→markdown), feature-flag editor(#19, toggle+의존성 경고+diff copy), prompt tuner(#20, 변수 슬롯→라이브 재렌더).
- 필수 요소:
  - **데이터는 정적 DOM**으로 먼저 렌더(invariant 8). JS는 재배열/토글/재계산만.
  - **export control 최소 1개**: "Copy as Markdown" / "Copy as JSON" / "Copy diff" / "Download .md" 중 하나 이상.
    export 텍스트는 *현재 UI 상태*를 반영.
  - 의존성/검증 경고(#19): 토글이 다른 값을 깨면 인라인 경고.
- content-loss 규칙 완화: 이건 문서 미러가 아니라 도구다. 단 **source 데이터 항목은 빠짐없이** 들어가야 한다.

### 3c. Deck / explainer 모드 (opt-in, 가벼운 JS)
- slide deck(#13): 키보드 화살표 네비, 슬라이드 카운터. **no-JS fallback = 슬라이드 세로 스택**(invariant 8).
- concept explainer(#15): 인터랙티브 시각화(인라인 SVG 조작) + glossary + TL;DR.
- JS 범위 제한: 네비게이션/토글/단순 상태만. 외부 의존성 0.

### 3d. Sandbox / prototype 모드 (opt-in JS)
- animation sandbox(#09): slider → **라이브 미리보기** → **copy params**(현재 값/CSS를 클립보드로).
- design system(#07)/component variants(#08): swatch/토큰/상태 contact sheet. 토큰 클릭 시 값 copy.
- clickable flow(#10): 링크된 화면들.
- 정의적 특징: **param → preview → copy** 루프. 사용자가 고른 값이 다시 프롬프트로 들어간다.

## 4. Asset 레이아웃 & 컨벤션

skill **자산은 여러 파일**이어도 되고(에이전트가 조립), **산출물만 단일 파일**이면 된다.

```
md-to-html/
  SKILL.md
  assets/
    base.html                 # 공유 shell = 현 template.html을 정리·이관 (document 모드 skeleton)
    components/               # 스니펫 라이브러리 (각 파일 = 자기완결 HTML+CSS(+JS) 조각, 헤더 주석 포함)
      tabs.html              # :target/details 기반 정적 탭
      diff-view.html         # margin 주석 + severity diff
      chart-svg.html         # 데이터→inline SVG 막대/스파크라인
      slide-deck.html        # 키보드 네비 + no-JS 스택 fallback
      triage-board.html      # draggable card + copy-as-markdown
      toggle-editor.html     # flag toggle + 의존성 경고 + copy-diff
      prompt-tuner.html      # 변수 슬롯 → 라이브 재렌더 + copy
      slider-sandbox.html    # slider → 라이브 preview → copy-params
      export-primitives.js   # copyToClipboard()/downloadFile() 레퍼런스 (산출물에 인라인 복사)
  scripts/
    validate_output.py        # mode-aware로 확장 (아래 §5)
  evals/
    evals.json
    files/                    # 모드별 fixture .md
```

조립 규칙(SKILL.md에 명시):
- `base.html`에서 시작 → 필요한 component 스니펫의 CSS를 `<style>`에, JS를 하나의 `<script>`에 인라인.
- **충돌 방지 네임스페이스**: component 클래스는 `mdh-` prefix(`.mdh-deck`, `.mdh-board`), JS는 단일 `window.MDH` 네임스페이스 + IIFE.
- **export 프리미티브(레퍼런스 코드 — 구현자가 재발명하지 않도록)**:

```js
// file:// 에서도 동작하도록 clipboard API + execCommand fallback
window.MDH = window.MDH || {};
MDH.copy = (text) => {
  if (navigator.clipboard && window.isSecureContext) {
    navigator.clipboard.writeText(text).catch(() => MDH._legacyCopy(text));
  } else { MDH._legacyCopy(text); }
};
MDH._legacyCopy = (text) => {
  const ta = document.createElement('textarea');
  ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
  document.body.appendChild(ta); ta.select();
  try { document.execCommand('copy'); } finally { ta.remove(); }
};
MDH.download = (name, text, type='text/markdown') => {
  const blob = new Blob([text], {type});
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob); a.download = name;
  a.click(); URL.revokeObjectURL(a.href);
};
```

- escape 헬퍼도 인라인으로 제공(invariant 10): 텍스트는 `textContent`, 속성은 escape.

## 5. Validator 변경 (`scripts/validate_output.py`, stdlib only)

현재 validator는 `<script>`를 무조건 금지한다. JS opt-in 때문에 **mode-aware**로 바꾼다.

신규 CLI:
```
python md-to-html/scripts/validate_output.py \
  --mode {document,editor,deck,sandbox} \   # 기본 document
  --source <md> --html <html> \
  [--peer <html>] [--require-modmap] [--forbid-svg] [--require-export]
```

검사 매트릭스:

| 검사 | document | editor | deck | sandbox |
| --- | --- | --- | --- | --- |
| `{{…}}` placeholder 없음 | ✔ | ✔ | ✔ | ✔ |
| 외부 `<link>` / 원격 `src·href` / `@import url(http)` 없음 | ✔ | ✔ | ✔ | ✔ |
| **네트워크 호출 없음** (`fetch(`,`XMLHttpRequest`,`WebSocket`,`EventSource`,`sendBeacon`, URL `import(`) | ✔ | ✔ | ✔ | ✔ |
| `<script src=…>` (외부 JS) 없음 | ✔ | ✔ | ✔ | ✔ |
| 인라인 `<script>` 허용 | ✘(없어야) | ✔ | ✔ | ✔ |
| footer `Source:` + source 경로 참조 | ✔ | ✔ | ✔ | ✔ |
| source heading → anchor 존재 | ✔ | – | – | – |
| code fence 수 ≤ `<pre>`/`<code>` 수 | ✔ | – | – | – |
| `--require-modmap` → `figure.modmap > svg` | opt | – | – | – |
| `--forbid-svg` | opt | – | – | – |
| peer link 파일명 존재 | opt | opt | opt | opt |
| **export affordance**(`--require-export`): copy/export/download 버튼 + `MDH.copy`/`MDH.download` 존재 | – | ✔ | opt | ✔ |
| **progressive enhancement(soft)**: deck은 slide DOM ≥ N, editor는 데이터 행 DOM 존재 → 없으면 warn | – | warn | warn | – |

구현 메모:
- 기존 `check()`를 모드 분기로 감싼다. document 모드는 현재 로직 그대로 + 네트워크 ban 추가.
- 네트워크 ban은 새 invariant 9의 핵심 안전장치 — JS를 허용하는 대가로 반드시 강제.
- progressive-enhancement는 정적 grep으로 완전 검증 불가 → soft warning + 수동 확인으로 명시.
- exit code: error 있으면 1, warn만 있으면 0(이지만 stderr 출력).

## 6. Evals & fixtures

`evals/evals.json`에 모드별 케이스. 기존 3개는 document 케이스로 이관(parity 확인용).

이관(document):
1. `document/rich-plan` — `require_modmap` (기존 test1).
2. `document/linked-pair` — peer link (기존 test2 plan+detail).
3. `document/prose-rfc` — `forbid_svg`, 절제 (기존 test3).

신규:
4. `document/tabbed-explainer` — collapsible/tab, content loss 0, 정적(JS 없이 `:target` 탭). (#14)
5. `editor/triage-board` — task에서 생성("이 티켓들로 triage board"), draggable + copy-as-markdown. assertions: `require_export`, 데이터 DOM 존재, 네트워크 0. (#18)
6. `editor/feature-flags` — toggle + 의존성 경고 + copy-diff. assertions: `require_export`, 네트워크 0. (#19)
7. `deck/slide-deck` — 키보드 네비 + no-JS 스택 fallback. assertions: slide DOM ≥ N, key handler 존재, 외부 자산 0. (#13)
8. `sandbox/slider` — 파라미터 있는 spec → slider + 라이브 preview + copy-params. assertions: `require_export`, 네트워크 0. (#09)

각 케이스 `assertions`에 `mode` 필드 추가. 신규 입력 fixture(`evals/files/`)도 함께 작성:
`test4_tabbed_explainer.md`, `test5_triage_tickets.md`, `test6_feature_flags.md`, `test7_deck_outline.md`, `test8_slider_spec.md`.

## 7. Migration / deprecation (md-to-spatial-html 제거)

- `assets/template.html` → 정리하여 `md-to-html/assets/base.html`로 이관.
  - 이관 시 기존 prior plan(`20260528_*.md`)이 지적한 정리도 반영: 보이는 영역 placeholder 안전화, glossary 없으면 생략 주석, scenario-matrix 범용 grid, modmap 긴 경로는 아래 prose로, negative letter-spacing 제거(이미 0).
- 기존 evals 3개 + validator → 새 skill로 이관/확장.
- `md-to-spatial-html/` 디렉터리 **삭제**(successor 결정에 따름).
- 참조 업데이트:
  - `README.md` skill 목록: `md-to-spatial-html` 항목 → `md-to-html`로 교체(4개 모드 설명 반영).
  - SKILL.md description(아래 §8)이 기존 trigger("이거 HTML로", "spatial html version" 등)를 모두 흡수하도록.
  - prior plan `20260528_*.md`는 **project memory로 보존**(역사적 기록). 본 계획이 그 forward-looking 부분을 대체함을 본 문서가 명시.
- `CLAUDE.md`/`AGENTS.md`에 `md-to-spatial-html` 경로 하드코딩이 있으면 교체(확인 필요 — 현재는 skills-ref 안내만 있고 직접 경로 참조는 없음).

## 8. SKILL.md frontmatter (초안)

```yaml
name: md-to-html
description: >-
  Convert markdown (plans, specs, design docs, reviews) — or a direct request —
  into a self-contained, single-file HTML artifact next to the source. Four modes:
  (1) document: static spatial doc with sidebar TOC, inline SVG module maps,
  risk/decision/comparison cards (the former md-to-spatial-html behavior);
  (2) editor: purpose-built interactive tools (triage board, feature-flag editor,
  prompt tuner) with copy/export-back-to-Claude; (3) deck: keyboard-navigable
  slides & concept explainers; (4) sandbox: slider/param prototypes with live
  preview and copy-params. Static (no-JS) is the default; vanilla JS unlocks only
  for interactive modes — always single file, no CDN, no network. Use for "make
  this HTML", "convert to HTML", "이거 HTML로", "plan을 HTML로", "triage board",
  "slide deck", "prompt tuner", "animation sandbox". Not for single-paragraph
  notes or passing mentions of HTML. Keywords: spatial html, interactive html,
  triage board, slide deck, prompt tuner, export to clipboard, self-contained.
```

본문 섹션 순서: Thesis → **Mode router** → Non-negotiable invariants(10) → Per-mode playbook(4) → Self-contained/JS rules → Workflow → Verification checklist(모드별 validator 호출) → Anti-patterns → Migration note.

Anti-patterns(기존 계승 + 신규):
- pandoc식 1:1 변환 / file 섹션을 스타일 리스트로 / 외부폰트·CDN / 원문 누락 / unescape / `.md` 삭제 (계승)
- **JS가 fetch·beacon으로 네트워크 호출** (금지)
- **JS 꺼지면 빈 화면**(progressive enhancement 위반)
- **export 없는 editor**(양방향 루프가 핵심인데 누락)
- **평범한 문서에 interactive 모드 over-fire** (router 기본은 document)
- 사용자 데이터에 `innerHTML` (XSS)

## Test plan

1. `uv run --directory skills-ref skills-ref validate ../md-to-html/` — frontmatter 스펙 통과.
2. `uv run --directory skills-ref skills-ref to-prompt ../md-to-html/` — description 렌더 확인, 다른 skill과 trigger 충돌 점검.
3. `python md-to-html/scripts/validate_output.py --help` 동작.
4. validator positive/negative fixture(임시 디렉터리 HTML):
   - placeholder 잔존 → fail
   - 원격 link/`fetch(` → fail (전 모드)
   - document 모드에 `<script>` → fail / editor 모드에 `<script>` → pass
   - editor 모드 export 버튼 없음(`--require-export`) → fail
   - deck slide DOM 없음 → warn
   - file layout인데 modmap 없음(`--require-modmap`) → fail / prose RFC에 SVG(`--forbid-svg`) → fail
   - peer link 누락 → fail / code block 누락(document) → fail
5. 이관된 document evals 3개로 기존 skill 대비 parity 확인.
6. 모드별 샘플 1개씩 브라우저로 더블클릭 → 오프라인 동작 + **JS off 상태에서 콘텐츠 보임** 수동 확인.

## Assumptions

- 산출물은 여전히 **agent가 base+snippet으로 조립**한다. 결정적(deterministic) md→html 변환기는 만들지 않는다.
- validator는 Python stdlib only 유지.
- 차트/시각화는 라이브러리 없이 **inline SVG**. CDN 차트 라이브러리는 self-contained 위반이라 금지.
- 산출물 단일 파일 / skill 자산은 다파일 조립 — 이 구분을 SKILL.md가 명시.
- progressive enhancement·XSS는 정적 grep으로 완전 검증 불가 → validator는 best-effort, 최종은 수동/리뷰.

## Risks

| 위험 | 완화 |
| --- | --- |
| interactive 모드가 평범한 문서에 over-fire | router 기본 document, interactive는 명시적 신호 + anti-pattern 명시 |
| 단일 파일에 여러 snippet 붙일 때 CSS/JS 충돌 | `mdh-` prefix + `window.MDH` 네임스페이스 + IIFE 컨벤션 |
| JS가 마크다운/사용자 텍스트를 innerHTML로 echo → XSS | invariant 10 + `textContent` 규칙 + validator soft check |
| `navigator.clipboard`가 `file://`에서 막힘 | `execCommand('copy')` textarea fallback 레퍼런스 제공 |
| "JS 없이 동작" 자동 검증 불가 | validator soft warn + 수동 브라우저 확인 |
| 네트워크 호출 누락 검출 회피(난독화) | 흔한 API 토큰 grep으로 1차 방어 + 외부 src/href ban; 완전 방어는 아님 명시 |
| skill scope 비대 → 유지보수 부담 | base 1개 + snippet 라이브러리로 모듈화, transform table 등 검증된 부분 그대로 계승 |

---
*본 계획은 `20260528_md_to_spatial_html_skill_improvement.md`의 forward-looking 부분을 대체한다(그 문서는 history로 보존).*
*Sources: [blog](https://claude.com/blog/using-claude-code-the-unreasonable-effectiveness-of-html), [html-effectiveness](https://github.com/ThariqS/html-effectiveness), 갤러리 카탈로그 #01–#20.*

---

## Review (2026-06-25)

`md-to-html` skill 구현 이후 구조·품질 리뷰 결과. 별도 대화에서 개선시 참고.

### 1. `agents/openai.yaml` 누락 (중요도: 중)
- SKILL.md frontmatter description은 잘 작성됨.
- 하지만 `agents/openai.yaml`이 존재하지 않아, skill 목록 UI용 `display_name`, `short_description`, `default_prompt`가 생성되지 않음.
- **개선**: `scripts/generate_openai_yaml.py` 실행하여 `agents/openai.yaml` 생성.

### 2. Component 템플릿이 완전한 HTML 문서임 (중요도: 중)
- `triage-board.html`, `slide-deck.html`, `slider-sandbox.html`, `toggle-editor.html`, `prompt-tuner.html` 등 모두 `<!doctype html>` ~ `</html>`로 감싸진 완전한 문서.
- SKILL.md는 "component 스니펫의 CSS를 `<style>`에, JS를 `<script>`에 인라인"이라고 지시하지만, 템플릿 자체가 독립 문서라 Codex가 CSS/JS 부분만 추출해야 함.
- **개선 옵션 A**: 템플릿을 스니펫-only로 변환 (CSS + JS만, 문서 래퍼 제거).
- **개선 옵션 B**: 템플릿 유지하되, SKILL.md에 "전체 문서에서 `<style>`과 `<script>` 블록만 추출하여 base.html에 인라인" 명시.
- 옵션 A가 더 안전함.

### 3. `base.html`이 467줄로 김 (중요도: 저)
- 모든 component 클래스의 CSS가 단일 파일에 있음. document 모드에서는 JS가 필요 없는 컴포넌트만 사용하므로 불필요한 CSS가 컨텍스트에 로딩될 수 있음.
- **개선**: `base.html`은 최소 shell(레이아웃, 기본 타이포그래피, footer)만 포함하고, component별 CSS는 `components/`에서 인라인하는 방식으로 분리. 또는 주석 처리하여 기본 visible로 두고 필요시 활성화하는 방식.

### 4. Validation script 미검증 (중요도: 중)
- `scripts/validate_output.py`는 작성되었으나 실제 생성된 HTML로 테스트되지 않음.
- `evals/` 폴더에 테스트 입력(fixture)은 있지만, 실행 결과나 expected output 아티팩트가 없음.
- **개선**: 실제 eval fixture로 validator 실행하여 모든 체크가 올바르게 동작하는지 확인.

### 5. SKILL.md 본문 언어 (중요도: 저)
- frontmatter description은 영어로 명확함.
- 본문(body)은 한국어로 작성됨. trigger description이 영어+한국어 혼합이라 양쪽 언어 사용자를 모두 커버하지만, Codex 컨텍스트에 한국어가 로드됨.
- **개선**: 한국어 사용자가 주 대상이면 유지. 다국어 지원을 원하면 핵심 워크플로우만 영어로 번역 또는 병기.

### 6. `evals/` 폴더는 개발 아티팩트 (중요도: 저)
- `evals/evals.json`과 `evals/files/`는 skill 스펙에 포함되지 않는 개발용 테스트 디렉터리.
- 스킬 외부로 분리하거나, skill 배포시 제외하는 것이 좋음.
- **개선**: `evals/`를 `md-to-html/` 외부로 이동하거나 `.gitignore`/스킬 제외 목록에 추가.

### 7. `init_skill.py` / `generate_openai_yaml.py` 미참조 (중요도: 저)
- 스킬 생성 가이드에 언급된 스크립트들이 이 스킬 디렉터리에 없음 (레포 루트에 있음).
- **개선**: 별도 문제 아님. 다만 스킬 내부에 스크립트 경로를 명시하면 신규 기여자가 찾기 쉬움.

### 8. Anti-patterns 섹션 충분함 (중요도: —)
- Pandoc 1:1 변환, 외부 CDN, innerHTML XSS, export 없는 editor 등 주요 실패 패턴이 잘 커버됨.

### 9. Invariant 설계 우수 (중요도: —)
- 10개 non-negotiable invariants이 명확하고 검증 가능. 네트워크 ban, progressive enhancement, XSS 방지 등 핵심 안전장치가 잘 배치됨.

### 10. Mode Router 설계 합리적 (중요도: —)
- 기본 document + opt-in interactive. 애매하면 document. peer link 연결. 과용 방지.
- **개선 제안**: router 표에 "원고가 두 모드를 동시에 요구하면 별도 파일로 분할" 규칙이 있지만, 예시가 없음. `test2_plan.md` + `test2_detail.md`가 이미 peer link 케이스로 있으니, router 예시로 추가하면 Codex가 더 명확히 이해할 수 있음.

---

## Triage / Resolution (2026-06-25, Claude)

위 opencode/skill-creator 리뷰를 이 레포 실제 컨벤션에 비춰 분류한 결과. 근거는 레포 내 다른 skill 구조 확인(`git-workflow`, `review-pr`, `algorithm-doc-kr`).

| # | 판정 | 근거 / 조치 |
| --- | --- | --- |
| 1 `agents/openai.yaml` 누락 | **거부 (해당 없음)** | `agents/`+`openai.yaml`은 `.system/*`(번들 시스템 skill)에만 존재. 이 레포에서 직접 작성한 skill은 전부 `SKILL.md`만 가짐. 검증은 `skills-ref`가 담당하며 통과함. opencode 평가기의 자기 포맷 기준 false positive. |
| 2 component가 완전 HTML 문서 | **적용함** | 사실 확인: 정적 3개(tabs/diff/chart)=fragment, 인터랙티브 5개(triage/toggle/prompt/deck/slider)=full-document. SKILL.md를 모드별 두 조립 경로로 수정 — document는 base.html+fragment 인라인, editor/deck/sandbox는 full-document 컴포넌트를 skeleton으로 복사·적응. 이게 에이전트가 실제 만든 구조와 일치하고 더 합리적. |
| 3 base.html 467줄 | **보류** | 기존 `template.html`(~457줄)과 동급. component별 CSS 분리는 조립 복잡도만 늘고 이득 적음. |
| 4 validator 미검증 | **이미 해결** | fixture로 라이브 검증 완료(network ban, document/editor script 분기, require-export, forbid-svg, require-modmap). LLM-run eval이라 결정적 산출 아티팩트는 미포함. |
| 5 본문 한국어 | **유지** | 주 사용자 한국어. frontmatter description은 영어+한국어 트리거 병기라 양쪽 커버. |
| 6 evals/ 분리 | **거부 (컨벤션 일치)** | `algorithm-doc-kr/evals`가 이미 skill 디렉터리 내장. evals 내장이 이 레포 컨벤션. |
| 7 init/generate 스크립트 미참조 | **거부 (해당 없음)** | 해당 스크립트는 `.system/skill-creator/scripts/`의 시스템 도구. 작성 skill에 포함 대상 아님. |
| 8·9 anti-patterns·invariants 우수 | 조치 없음 | 긍정 피드백. |
| 10 router 분할 예시 부재 | **적용함** | router에 "계획(document)+백로그 보드(editor) → 별도 파일+peer link" 구체 예시, 그리고 같은 모드 형제(`test2_plan`+`test2_detail`) 예시 추가. |

적용 대상은 **#2, #10** 두 건이며 모두 `md-to-html/SKILL.md`에 반영함. 나머지는 위 근거로 거부/보류/기해결.
