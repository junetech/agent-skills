---
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
---

# md → HTML

단일 skill이 입력/요청의 성격을 보고 4개 모드 중 하나를 골라, **단일 파일 self-contained HTML** 산출물을 원본 옆에 만든다.

Thesis (Thariq Shihipar, [html-effectiveness](https://thariqs.github.io/html-effectiveness/)):

> Diffs and call-graphs are spatial information; markdown flattens them. HTML's real power: (1) information density/spatiality, (2) interactivity, (3) a two-way loop where the user edits and exports back to Claude.

**산출물만 단일 파일.** skill 자산(`assets/`, `scripts/`)은 다파일 구조여도 된다. 조립 방식은 모드에 따라 다르다 — document 모드는 `base.html` shell에 정적 fragment를 인라인하고, interactive 모드(editor/deck/sandbox)는 해당 full-document 컴포넌트를 skeleton으로 복사해 적응시킨다 (자세히는 아래 Self-contained / JS Rules).

---

## Mode Router

라우팅 기본값은 **document**. interactive 모드는 "사용자가 *도구*를 원한다"가 분명할 때만.

| 신호 (source/요청) | 모드 | JS |
| --- | --- | --- |
| plan / spec / design doc / RFC / postmortem / review / "이거 HTML로", "render this", "spatial HTML version", "plan을 HTML로" | **document** (기본) | 없음 (정적) |
| "triage board / kanban / 우선순위 보드", "toggle/flag editor", "prompt tuner", 편집·재배열·export가 목적 | **editor** | opt-in |
| "slide deck / 발표자료 / deck", "concept explainer", 순차 제시·교육 | **deck** | opt-in (네비/토글 한정) |
| "animation sandbox / 파라미터 튜닝", "design system / swatches", "component variants", 값 조절→미리보기 | **sandbox** | opt-in |

라우팅 규칙:
- 애매하면 **document**.
- 한 요청이 두 모드를 요구하면 **각각 별도 파일**로 만들고 peer link로 연결한다. 한 파일에 섞지 않는다.
  - 예: "이 스프린트 계획을 HTML로 만들고 백로그는 트리아지 보드로" → `sprint_plan.html`(document) + `backlog_board.html`(editor), 양쪽 sidebar에서 서로 링크.
  - 같은 모드의 형제 문서(예: `test2_plan.md` + `test2_detail.md`)는 둘 다 document 모드로 만들고 peer link로 연결한다.

---

## Non-negotiable Invariants

1. **`.md`를 보존한다.** Source of truth. 같은 basename `.html`을 같은 디렉터리에 쓴다. 절대 덮어쓰지/지우지 않는다.
2. **단일 self-contained 파일.** CSS는 `<style>` 인라인, SVG 인라인, JS는 `<script>` 인라인. CDN/외부폰트/네트워크 금지. 더블클릭으로 오프라인 동작.
3. **document 모드는 content loss 0.** 모든 문단/코드/표/리스트가 escaped HTML로 살아남는다.
4. **peer link** — 관련 파일 묶음 변환 시 sidebar에서 형제 문서를 링크.
5. **footer attribution** — 매 파일 끝 `Source: <path>.md (markdown remains authoritative; this HTML is a view).`
6. **markdown-origin text는 HTML escape** (`&`/`<`/`>`/속성 따옴표; 코드는 `<code>` 안에서 escape).
7. **file/module/architecture 섹션 → inline SVG module map** (`<figure class="modmap">`) + 원문 보존. 스타일 리스트나 파일명 `<table>`로 대체 금지. SVG 박스 안 레이블은 짧게; 긴 전체 경로와 원문 불릿은 figure 아래 escaped prose 또는 table로 보존.
8. **Progressive enhancement.** JS는 점진적 향상이어야 한다 — JS가 꺼져도 핵심 콘텐츠가 보여야 한다. deck은 슬라이드가 세로로 쌓여 보이고, editor/board는 데이터가 정적 리스트로 보인다. **JS 없으면 빈 화면 = 실패.** 콘텐츠는 실제 DOM에 있어야 하고, JS가 `innerHTML`로 처음부터 생성하면 안 된다.
9. **No network / no exfiltration.** `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`, `navigator.sendBeacon`, URL `import()`, 원격 `src/href`, `@import url(http…)` **전부 금지.** export는 clipboard 쓰기 또는 로컬 파일 download만.
10. **No XSS via echoed text.** 사용자/markdown 텍스트를 DOM에 넣을 때 `textContent`/escape 사용. 사용자 데이터에 `innerHTML` 사용 금지.

---

## Per-mode Playbook

### Document Mode (기본, 정적)

기존 `md-to-spatial-html` 변환을 그대로 계승 + 레벨업. JS 없음. `assets/base.html`에서 시작.

**The transform table** — markdown shape을 보면 HTML로 이렇게 렌더한다:

| Markdown shape | HTML rendering |
| --- | --- |
| Bullet list of regions / states / phases along an axis | **Inline SVG** with labeled colored bands on a horizontal axis |
| "Option A vs Option B; A is the one we picked" | **Side-by-side comparison cards** with ✓/✗ headers, accent borders |
| 2-axis grid of variants (e.g. `unfixed × pf_method`) | **Matrix grid** (CSS grid, 2D cells, `--matrix-cols` custom property) instead of a flat markdown table |
| Numbered list of risks / concerns | **Risk cards** with color-coded severity badges (red/amber/green) and a left border in the same color |
| "Decision: X. Reason: Y. Scope: Z." patterns | **Decision strip**: `key | value` rows with accent left border |
| File/module/class relationships (load-bearing — see invariant 7) | **Inline SVG module map** plus preserved source text — mandatory, not optional. Boxes & arrows with arrowhead markers, grouped by zone (new / existing / external) when there are >1 zones. Not a styled list. Not a `<table>` of filenames. |
| Sequence / pipeline / data flow | **Horizontal flow row** with step chips and arrow separators |
| Long pseudocode / config block (>30 lines) | `<details open>` wrapping a `<pre>` so it can be folded |
| Acronyms / domain jargon | **Glossary list at the bottom of the sidebar** (omit block entirely if no acronyms) |
| Cross-references to other docs | **Sidebar peer links** at top, inline anchor jumps in body |
| "TL;DR" / "At a glance" intro paragraph | **Highlighted TL;DR box** at the top, info-colored, with bulleted summary |
| "Out of scope / Deferred" items | Decision-strip variant with **muted gray** styling + `deferred` badge |

레벨업 컴포넌트 (정적, JS 불필요):
- **Tabbed code/content**: `:target` 또는 `<details>` 기반 — `assets/components/tabs.html` 참조
- **Annotated diff**: `<pre>` + margin gutter + severity 색상 — `assets/components/diff-view.html` 참조
- **Inline-SVG chart**: 소스에 데이터가 있을 때만 — `assets/components/chart-svg.html` 참조
- **Timeline**: 사건 분 단위 세로 타임라인

### Editor Mode (opt-in JS)

정의적 특징: **사용자의 편집을 다시 Claude로 가져갈 수 있어야 한다.** export 없는 editor는 실패다.

- 참조 컴포넌트: `assets/components/triage-board.html`, `toggle-editor.html`, `prompt-tuner.html`
- 필수 요소:
  - **데이터는 정적 DOM**으로 먼저 렌더 (invariant 8). JS는 재배열/토글/재계산만.
  - **export control 최소 1개**: "Copy as Markdown" / "Copy as JSON" / "Copy diff" / "Download .md" 중 하나 이상. export 텍스트는 *현재 UI 상태*를 반영.
  - `MDH.copy`/`MDH.download` export 프리미티브 사용 — `assets/components/export-primitives.js` 참조
  - 의존성/검증 경고: 토글이 다른 값을 깨면 인라인 경고.
- content-loss 규칙 완화: 도구다. 단 **source 데이터 항목은 빠짐없이** 들어가야 한다.

### Deck / Explainer Mode (opt-in, 가벼운 JS)

- slide deck: 키보드 화살표 네비, 슬라이드 카운터. **no-JS fallback = 슬라이드 세로 스택** (invariant 8)
- concept explainer: 인터랙티브 시각화(인라인 SVG 조작) + glossary + TL;DR
- `assets/components/slide-deck.html` 참조
- JS 범위 제한: 네비게이션/토글/단순 상태만. 외부 의존성 0.

### Sandbox / Prototype Mode (opt-in JS)

정의적 특징: **param → preview → copy** 루프.

- animation sandbox: slider → 라이브 미리보기 → copy params (현재 값/CSS를 클립보드로)
- design system/component variants: swatch/토큰/상태 contact sheet. 토큰 클릭 시 값 copy.
- `assets/components/slider-sandbox.html` 참조
- 사용자가 고른 값이 다시 프롬프트로 들어간다.

---

## Self-contained / JS Rules

**Component 종류 두 가지** (`assets/components/`):
- **Fragment 스니펫** (정적, document 모드용): `tabs.html`, `diff-view.html`, `chart-svg.html` — CSS+마크업 조각. `base.html`에 인라인한다.
- **Full-document skeleton** (interactive, editor/deck/sandbox용): `triage-board.html`, `toggle-editor.html`, `prompt-tuner.html`, `slide-deck.html`, `slider-sandbox.html` — 그 자체가 더블클릭으로 열리는 완성 문서. 해당 모드에서는 이 파일을 **통째로 복사해 skeleton으로 쓰고** 내용을 적응시킨다 (`base.html`을 쓰지 않는다).

조립 규칙:
1. **document 모드**: `assets/base.html`에서 시작 → 필요한 fragment 스니펫의 CSS를 `<style>`에, (있으면) 마크업을 body에 인라인.
2. **editor/deck/sandbox 모드**: 모드에 맞는 full-document 컴포넌트를 복사 → source 데이터로 채우고 적응. `export-primitives.js`의 `MDH.*`가 이미 들어있지 않으면 `<script>` 맨 앞에 인라인.
3. **충돌 방지 네임스페이스**: component 클래스는 `mdh-` prefix (`.mdh-deck`, `.mdh-board`), JS는 단일 `window.MDH` 네임스페이스 + IIFE. (한 파일에 여러 컴포넌트를 합칠 때만 중요)
4. export 프리미티브 (`MDH.copy`, `MDH.download`)의 정본은 `assets/components/export-primitives.js`.
5. escape 헬퍼: 텍스트는 `textContent`, 속성은 escape. `innerHTML`은 **사용자 데이터에 절대 금지**.

JS 허용 범위 (invariant 9):
- **금지**: `fetch(`, `XMLHttpRequest`, `WebSocket`, `EventSource`, `navigator.sendBeacon`, URL `import()`, 원격 `src`/`href`, `@import url(http…)`
- **허용**: `navigator.clipboard.writeText`, `document.execCommand('copy')`, `URL.createObjectURL`+`<a>.click()`로 로컬 파일 다운로드

---

## Workflow

1. **Read every source .md in full.** No summarizing, no skimming.
2. **Route the mode.** Plan/spec/doc → document. Explicit tool request → editor/deck/sandbox.
3. **List the spatial moments.** 모든 flatten된 2D/관계 콘텐츠를 찾는다. (document mode)
4. **Plan the sidebar.** Sections (anchor list) + glossary (acronyms) + peer links. Section labels: 240px에 맞게 짧게.
5. **Pick the skeleton by mode.** document → `assets/base.html` + inline fragment snippets (tabs/diff/chart). editor/deck/sandbox → copy the matching full-document component (`triage-board`/`toggle-editor`/`prompt-tuner`/`slide-deck`/`slider-sandbox`) and adapt it.
6. **Fill the body** per source. Escape markdown-origin text, replace placeholders, delete unused example snippets, add components per transform table.
7. **Verify before reporting done** (see Verification checklist below).

---

## Verification Checklist

**All modes:**
```
python md-to-html/scripts/validate_output.py \
  --mode {document|editor|deck|sandbox} \
  --source <source.md> --html <output.html>
```
Add flags as applicable: `--peer <peer.html>`, `--require-modmap`, `--forbid-svg`, `--require-export`.

**Document mode 추가 점검:**
- Every .md section has an HTML counterpart (use .md TOC as checklist).
- Every code block survived (count them).
- File opens standalone — no `<link>`, no `<script src=...>`, no remote asset URLs.
- No `{{...}}` placeholder remains.
- Sidebar anchor links match `id` attributes in body.
- Footer attribution line present.
- SVG audit (invariant 7): file-layout/module/architecture section → `<figure class="modmap">` containing `<svg>`.

**Editor/sandbox mode 추가 점검:**
- Export control exists (copy/download button).
- `MDH.copy` or `MDH.download` in the `<script>` block.
- Data items from source all present in DOM.
- No network calls (`fetch(`, `XMLHttpRequest`, etc.).
- JS-off: data visible as static list/table.

**Deck mode 추가 점검:**
- Slide DOM elements present (`.mdh-slide` or equivalent).
- Key handler (arrow keys) in `<script>`.
- No-JS fallback: slides stack vertically.

---

## Anti-patterns

- **Pandoc-style 1:1 변환** — 선형 구조 유지. 이 skill은 *shape transformation*.
- **File/module 섹션을 styled list로** (`.file-list`, `.file-row` 등) — invariant 7가 막는 실패 패턴. SVG module map 그려라.
- **외부 폰트 / CDN** — 더블클릭+오프라인 파괴.
- **JS가 fetch·beacon으로 네트워크 호출** — 완전 금지.
- **JS 꺼지면 빈 화면** — progressive enhancement 위반 (invariant 8).
- **export 없는 editor** — 양방향 루프가 핵심인데 누락 (invariant: editor mode requires export).
- **평범한 문서에 interactive 모드 over-fire** — router 기본은 document.
- **사용자 데이터에 `innerHTML`** — XSS (invariant 10).
- **원문 누락 / unescape** — prose가 diagram으로 대체되면 안 됨.
- **`.md` 삭제 또는 덮어쓰기** — never.
- **Generic titles** — 문서 실제 제목 사용; 없으면 파일명에서 파생.

---

## Migration Note

이 skill은 `md-to-spatial-html`의 후속(successor)이다. 기존 document 변환은 **document 모드**로 그대로 살아남는다. `md-to-spatial-html` 디렉터리는 제거됨. 기존 트리거("이거 HTML로", "spatial HTML version", "plan을 HTML로" 등)는 모두 이 skill이 흡수한다.

Prior plan `vault/plans/20260528_md_to_spatial_html_skill_improvement.md`는 역사적 기록으로 보존. 본 skill의 `vault/plans/20260625_md_to_html_skill.md`가 그 forward-looking 부분을 대체한다.
