---
name: md-to-html
description: >-
  Convert markdown (plans, specs, design docs, reviews) — or a direct request —
  into a self-contained, single-file HTML artifact next to the source. Four modes:
  (1) document: static spatial doc with sidebar TOC, inline SVG module maps,
  risk/decision/comparison cards;
  (2) editor: purpose-built interactive tools (triage board, feature-flag editor,
  prompt tuner) with copy/export-back-to-Claude;
  (3) deck: keyboard-navigable slides & concept explainers;
  (4) sandbox: slider/param prototypes with live preview and copy-params.
  Static (no-JS) is the default; vanilla JS unlocks only for interactive modes —
  always single file, no CDN, no network.
  Use for "make this HTML", "convert to HTML", "render this plan as HTML",
  "triage board", "slide deck", "prompt tuner", "animation sandbox", or similar.
  Not for single-paragraph notes or passing mentions of HTML.
  Keywords: spatial html, interactive html, triage board, slide deck, prompt tuner,
  export to clipboard, self-contained.
---

# md → HTML

Inspect the input/request, pick one of four modes, and produce a **single-file self-contained HTML** artifact next to the source.

Thesis (Thariq Shihipar, [html-effectiveness](https://thariqs.github.io/html-effectiveness/)):

> Diffs and call-graphs are spatial information; markdown flattens them. HTML's real power: (1) information density/spatiality, (2) interactivity, (3) a two-way loop where the user edits and exports back to Claude.

**Only the output is a single file.** Skill assets (`assets/`, `scripts/`) may be multi-file. Assembly differs by mode — document mode inlines static fragments into the `base.html` shell, while interactive modes (editor/deck/sandbox) copy the matching full-document component as a skeleton and adapt it (details under Self-contained / JS Rules below).

---

## Mode Router

The routing default is **document**. Use an interactive mode only when it is clear that the user wants a *tool*.

| Signal (source/request) | Mode | JS |
| --- | --- | --- |
| plan / spec / design doc / RFC / postmortem / review / "make this HTML", "render this", "spatial HTML version", "turn the plan into HTML" | **document** (default) | none (static) |
| "triage board / kanban / priority board", "toggle/flag editor", "prompt tuner", anything whose purpose is editing, reordering, or exporting | **editor** | opt-in |
| "slide deck / presentation / deck", "concept explainer", sequential presentation or teaching | **deck** | opt-in (navigation/toggle only) |
| "animation sandbox / parameter tuning", "design system / swatches", "component variants", adjust-value-then-preview | **sandbox** | opt-in |

Routing rules:
- When ambiguous, choose **document**.
- If one request calls for two modes, produce **separate files** and connect them with peer links. Never mix modes in one file.
  - Example: "turn this sprint plan into HTML and make the backlog a triage board" → `sprint_plan.html` (document) + `backlog_board.html` (editor), cross-linked from both sidebars.
  - Sibling documents in the same mode (e.g. `test2_plan.md` + `test2_detail.md`) both become document mode and are connected with peer links.

---

## Non-negotiable Invariants

1. **Preserve the `.md`.** It is the source of truth. Write the `.html` with the same basename into the same directory. Never overwrite or delete the source.
2. **Single self-contained file.** CSS inline in `<style>`, SVG inline, JS inline in `<script>`. No CDN, no external fonts, no network. It must work offline on double-click.
3. **Document mode has zero content loss.** Every paragraph, code block, table, and list survives as escaped HTML.
4. **Peer links** — when converting a related set of files, link sibling documents from the sidebar.
5. **Footer attribution** — end every file with `Source: <path>.md (markdown remains authoritative; this HTML is a view).`
6. **Escape markdown-origin text** (`&`/`<`/`>`/attribute quotes; code is escaped inside `<code>`).
7. **File/module/architecture sections → inline SVG module map** (`<figure class="modmap">`) with the original text preserved. Never substitute a styled list or a `<table>` of filenames. Keep labels inside SVG boxes short; preserve long full paths and the original bullets below the figure as escaped prose or a table.
8. **Progressive enhancement.** JS must be a progressive enhancement — core content must be visible with JS disabled. A deck's slides stack vertically; an editor/board shows its data as a static list. **Blank screen without JS = failure.** Content must live in the real DOM, never generated from scratch by JS via `innerHTML`.
9. **No network / no exfiltration.** `fetch`, `XMLHttpRequest`, `WebSocket`, `EventSource`, `navigator.sendBeacon`, URL `import()`, remote `src`/`href`, `@import url(http…)` are **all forbidden.** Export means clipboard writes or local file downloads only.
10. **No XSS via echoed text.** Use `textContent`/escaping when putting user or markdown text into the DOM. Never use `innerHTML` with user data.

---

## Per-mode Playbook

### Document Mode (default, static)

Inherits the original `md-to-spatial-html` conversion and levels it up. No JS. Start from `assets/base.html`.

**The transform table** — given a markdown shape, render it in HTML like this:

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

Level-up components (static, no JS needed):
- **Tabbed code/content**: `:target`- or `<details>`-based — see `assets/components/tabs.html`
- **Annotated diff**: `<pre>` + margin gutter + severity colors — see `assets/components/diff-view.html`
- **Inline-SVG chart**: only when the source contains the data — see `assets/components/chart-svg.html`
- **Timeline**: vertical minute-by-minute timeline of events

### Editor Mode (opt-in JS)

Defining trait: **the user's edits must be able to travel back to Claude.** An editor without export is a failure.

- Reference components: `assets/components/triage-board.html`, `toggle-editor.html`, `prompt-tuner.html`
- Requirements:
  - **Render data as static DOM** first (invariant 8). JS only reorders, toggles, and recomputes.
  - **At least one export control**: "Copy as Markdown" / "Copy as JSON" / "Copy diff" / "Download .md". The exported text reflects the *current UI state*.
  - Use the `MDH.copy`/`MDH.download` export primitives — see `assets/components/export-primitives.js`
  - Dependency/validation warnings: if a toggle breaks another value, show an inline warning.
- The content-loss rule is relaxed here — this is a tool. But **every source data item** must be present.

### Deck / Explainer Mode (opt-in, light JS)

- slide deck: keyboard arrow navigation, slide counter. **no-JS fallback = slides stacked vertically** (invariant 8)
- concept explainer: interactive visualization (inline SVG manipulation) + glossary + TL;DR
- see `assets/components/slide-deck.html`
- JS scope limit: navigation, toggles, simple state only. Zero external dependencies.

### Sandbox / Prototype Mode (opt-in JS)

Defining trait: the **param → preview → copy** loop.

- animation sandbox: slider → live preview → copy params (current values/CSS to the clipboard)
- design system / component variants: swatch, token, and state contact sheet. Clicking a token copies its value.
- see `assets/components/slider-sandbox.html`
- The values the user picks must be able to go back into a prompt.

---

## Self-contained / JS Rules

**Two kinds of component** (`assets/components/`):
- **Fragment snippets** (static, for document mode): `tabs.html`, `diff-view.html`, `chart-svg.html` — CSS + markup pieces. Inline them into `base.html`.
- **Full-document skeletons** (interactive, for editor/deck/sandbox): `triage-board.html`, `toggle-editor.html`, `prompt-tuner.html`, `slide-deck.html`, `slider-sandbox.html` — each is already a complete document that opens on double-click. In those modes, **copy the whole file as the skeleton** and adapt its content (do not use `base.html`).

Assembly rules:
1. **document mode**: start from `assets/base.html` → inline the CSS of the needed fragment snippets into `<style>` and their markup (if any) into the body.
2. **editor/deck/sandbox mode**: copy the full-document component matching the mode → fill it with source data and adapt. If `MDH.*` from `export-primitives.js` is not already present, inline it at the top of the `<script>`.
3. **Collision-proof namespace**: component classes use the `mdh-` prefix (`.mdh-deck`, `.mdh-board`); JS uses a single `window.MDH` namespace inside an IIFE. (Only matters when combining several components in one file.)
4. The canonical source of the export primitives (`MDH.copy`, `MDH.download`) is `assets/components/export-primitives.js`.
5. Escape helpers: text goes through `textContent`, attributes are escaped. `innerHTML` is **absolutely forbidden for user data**.

JS scope (invariant 9):
- **Forbidden**: `fetch(`, `XMLHttpRequest`, `WebSocket`, `EventSource`, `navigator.sendBeacon`, URL `import()`, remote `src`/`href`, `@import url(http…)`
- **Allowed**: `navigator.clipboard.writeText`, `document.execCommand('copy')`, local file download via `URL.createObjectURL` + `<a>.click()`

---

## Workflow

1. **Read every source .md in full.** No summarizing, no skimming.
2. **Route the mode.** Plan/spec/doc → document. Explicit tool request → editor/deck/sandbox.
3. **List the spatial moments.** Find every flattened 2D/relational piece of content. (document mode)
4. **Plan the sidebar.** Sections (anchor list) + glossary (acronyms) + peer links. Keep section labels short enough to fit 240px.
5. **Pick the skeleton by mode.** document → `assets/base.html` + inline fragment snippets (tabs/diff/chart). editor/deck/sandbox → copy the matching full-document component (`triage-board`/`toggle-editor`/`prompt-tuner`/`slide-deck`/`slider-sandbox`) and adapt it.
6. **Fill the body** per source. Escape markdown-origin text, replace placeholders, delete unused example snippets, add components per transform table.
7. **Verify before reporting done** (see Verification checklist below).
8. **Suggest external links.** Links already present in the source carry over as-is into `<a href>` (a hyperlink is not an asset — it does not affect offline behavior). For any other spot where an external reference would help (a cited spec, paper, or tool doc), **do not insert it into the HTML on your own**; after generation, ask the user "should I link X in this section?"

---

## Verification Checklist

**All modes:**
```sh
# Linux / macOS
python3 <skill-dir>/scripts/validate_output.py \
  --mode {document|editor|deck|sandbox} \
  --source <source.md> --html <output.html>
# Windows
python <skill-dir>/scripts/validate_output.py ...
```
`<skill-dir>` is this skill's own directory — the harness reports it when loading the skill. A repo-relative path such as `md-to-html/scripts/...` only resolves inside this repository; the skill gets installed outside the repository it operates on.

Add flags as applicable: `--peer <peer.html>`, `--require-modmap`, `--forbid-svg`, `--require-export`.

**Document mode, additional checks:**
- Every .md section has an HTML counterpart (use .md TOC as checklist).
- Every code block survived (count them).
- File opens standalone — no `<link>`, no `<script src=...>`, no remote asset URLs on `img`/`iframe`/`source`. A remote `<a href>` hyperlink is fine.
- No template placeholder remains (`DOCUMENT_TITLE`, `TAB_1_ID`, …). A `{{KEY}}` marker is *not* a placeholder: in prompt-tuner it is a runtime variable and must survive into the output.
- Sidebar anchor links match `id` attributes in body.
- Footer attribution line present.
- SVG audit (invariant 7): file-layout/module/architecture section → `<figure class="modmap">` containing `<svg>`.

**Editor/sandbox mode, additional checks:**
- Export control exists (copy/download button).
- `MDH.copy` or `MDH.download` in the `<script>` block.
- Data items from source all present in DOM.
- No network calls (`fetch(`, `XMLHttpRequest`, etc.).
- JS-off: data visible as static list/table.

**Deck mode, additional checks:**
- Slide DOM elements present (`.mdh-slide` or equivalent).
- Key handler (arrow keys) in `<script>`.
- No-JS fallback: slides stack vertically.

---

## Anti-patterns

- **Pandoc-style 1:1 conversion** — keeps the linear structure. This skill is about *shape transformation*.
- **File/module sections as a styled list** (`.file-list`, `.file-row`, etc.) — the failure pattern invariant 7 exists to block. Draw the SVG module map.
- **External fonts / CDN** — breaks double-click-and-offline.
- **JS making network calls via fetch or beacon** — completely forbidden.
- **Blank screen when JS is off** — violates progressive enhancement (invariant 8).
- **Editor without export** — the two-way loop is the whole point (invariant: editor mode requires export).
- **Over-firing an interactive mode on an ordinary document** — the router default is document.
- **`innerHTML` with user data** — XSS (invariant 10).
- **Dropped or unescaped source text** — a diagram must never replace the prose.
- **Deleting or overwriting the `.md`** — never.
- **Generic titles** — use the document's real title; derive one from the filename if absent.

---

## Migration Note

This skill is the successor to `md-to-spatial-html`. The original document conversion survives unchanged as **document mode**. The `md-to-spatial-html` directory has been removed. All of its old triggers ("make this HTML", "spatial HTML version", "turn the plan into HTML", and the same phrases in other languages) are absorbed by this skill.

The prior plan `vault/plans/20260528_md_to_spatial_html_skill_improvement.md` is kept as a historical record. This skill's `vault/plans/20260625_md_to_html_skill.md` supersedes its forward-looking parts.
