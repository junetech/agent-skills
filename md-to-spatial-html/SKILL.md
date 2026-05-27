---
name: md-to-spatial-html
description: >-
  Convert one or more markdown files (typically plans, design docs, specs,
  reviews) into self-contained spatial HTML peers alongside the originals —
  sticky sidebar TOC, inline SVG diagrams, color-coded risk cards, comparison
  cards, scenario matrices — based on the html-effectiveness principles
  (https://thariqs.github.io/html-effectiveness/). Use when the user says "make
  this HTML", "convert to HTML", "spatial HTML version", "이거 HTML로 만들어",
  "plan을 HTML로", or similar. Always preserves the .md as the authoritative copy
  and writes the .html next to it. Not for single-paragraph notes, ad-hoc HTML
  mockups not derived from a .md, or passing mentions of HTML. Keywords:
  html-effectiveness, spatial html, sidebar TOC, inline SVG, plan to html,
  convert markdown.
---

# md → spatial HTML

Convert markdown into self-contained HTML peers that exploit the medium's spatial affordances. The thesis (Thariq Shihipar, [html-effectiveness](https://thariqs.github.io/html-effectiveness/)):

> Diffs and call-graphs are spatial information; markdown flattens them.

Your job: take a .md that flattens 2D/relational content into linear bullets, and re-render it as HTML that makes the shape visible at a glance — without dropping a single sentence of the original.

## Non-negotiable rules

1. **Keep the .md.** It's the source of truth. Write a sibling `.html` with the same basename, same directory. Never delete or overwrite the .md.
2. **One file, no externals.** Inline CSS in `<style>`. Inline SVG. No CDN fonts, no scripts (CSS handles sticky/collapsible). The .html must open by double-click anywhere.
3. **No content loss.** Every paragraph, code block, table cell, and list item in the .md must survive in the .html. You're adding spatial structure on top, not summarizing.
4. **Link the peers.** When converting a set of related files (plan + detail, etc.), each .html links to its siblings in the sidebar.
5. **Footer attribution.** End every generated file with `Source: <path>.md (markdown remains authoritative; this HTML is a spatial view).`
6. **File/module structure → inline SVG, not a styled list.** If the source describes how files, modules, packages, or components relate to each other (a "File layout" / "Module map" / "Architecture" / "What lives where" section), you MUST draw it as an inline `<svg>` boxes-and-arrows module map. Do not substitute a styled list (`.file-list`, `.file-row`, etc.) or a plain `<table>` of filenames — those flatten exactly the spatial information SVG exists to preserve. The template includes a `.modmap` starter snippet — use it. Before declaring the work done, search the source `.md` for `## File layout`, `## Module`, `## Architecture`, or similar; if any of those exist and your HTML has zero `<svg>` for that section, go back and draw it.

## When to fire vs not

- ✅ User points at one or more .md files and asks for "HTML", "spatial HTML", "render this", "html 버전".
- ✅ Plans, design docs, postmortems, spec docs, decision records, review notes.
- ❌ Single-paragraph notes (no spatial content to surface — markdown is already fine).
- ❌ Ad-hoc HTML mockups not derived from a .md source.
- ❌ Don't fire just because the user mentions HTML in passing.

## The transform table (the actual valuable part)

When you spot this shape in the markdown, render it as the HTML on the right. This is what separates a spatial conversion from a pandoc dump.

| Markdown shape | HTML rendering |
| --- | --- |
| Bullet list of regions / states / phases along an axis | **Inline SVG** with labeled colored bands on a horizontal axis |
| "Option A vs Option B; A is the one we picked" | **Side-by-side comparison cards** with ✓/✗ headers, accent borders |
| 2-axis grid of variants (e.g. `unfixed × pf_method`) | **Matrix grid** (CSS grid, 2D cells) instead of a flat markdown table |
| Numbered list of risks / concerns | **Risk cards** with color-coded severity badges (red/amber/green) and a left border in the same color |
| "Decision: X. Reason: Y. Scope: Z." patterns | **Decision strip**: `key | value` rows with accent left border |
| File/module/class relationships (load-bearing — see rule 6) | **Inline SVG module map** — mandatory, not optional. Boxes & arrows with arrowhead markers, grouped by zone (new / existing / external) when there are >1 zones. Not a styled list. Not a `<table>` of filenames. |
| Sequence / pipeline / data flow | **Horizontal flow row** with step chips and arrow separators |
| Long pseudocode / config block (>30 lines) | `<details open>` wrapping a `<pre>` so it can be folded |
| Acronyms / domain jargon | **Glossary list at the bottom of the sidebar** |
| Cross-references to other docs | **Sidebar peer links** at top, inline anchor jumps in body |
| "TL;DR" / "At a glance" intro paragraph | **Highlighted TL;DR box** at the top, info-colored, with bulleted summary |
| "Out of scope / Deferred" items | Decision-strip variant with **muted gray** styling + `deferred` badge |

## Workflow

1. **Read every source .md in full.** No summarizing, no skimming — you need the verbatim content to round-trip it.
2. **List the spatial moments.** Before writing any HTML, jot (mentally) every place the markdown is flattening something: lists that are actually diagrams, tables that are actually matrices, decisions that are actually cards, risks that need severity colors. This list drives your component choices.
3. **Plan the sidebar.** Sections (anchor list) + glossary (acronyms) + peer links (sibling docs). Keep section labels short — they have to fit in 240px.
4. **Copy `assets/template.html` from this skill directory** as the starting skeleton. It has all the CSS classes wired up: `.tldr`, `.card`, `.decision`, `.risk.sev-{high,med,low}`, `.scenario-matrix`, `.pipeline`, `.partition-fig`, `.modmap`, `.helpers`, etc.
5. **Fill the body** per the source .md. Replace placeholders, add components where the transform table calls for them.
6. **Verify before reporting done:**
   - Every .md section has an HTML counterpart (use the .md's TOC as your checklist).
   - Every code block survived (count them if uncertain).
   - The file opens standalone — no `<link href="...">`, no `<script src="...">`.
   - Sidebar anchor links match `id` attributes in the body.
   - Peer links resolve (when converting multiple files).
   - Footer attribution line is present.
   - **SVG audit (rule 6).** If the source has any file-layout / module / architecture section, your HTML has at least one `<svg>` for that section. If it doesn't, you're not done — go draw it before reporting.

## Iteration knobs

If the user has aesthetic preferences after seeing the first output, the template's `:root { --... }` color tokens are the right knobs to surface. Don't restyle by hand-editing individual rules — change the tokens.

If the user wants the HTML simpler (e.g. "drop the SVG, just use a table"), they're telling you the spatial transform was wrong for that section. Demote the diagram to a table; don't argue.

If the user wants it richer ("add a chart for the obj trajectory") — that's outside this skill's scope (no data dependency). Either embed a static SVG or punt to "I can render that with a real plotting tool if you give me the data."

## Anti-patterns

- **Pandoc-style conversion** — pandoc preserves linear shape. This skill is about *transforming* shape. If you find yourself writing 1:1 `<p>` ↔ paragraph, you've missed the point.
- **Inventing a styled list (`.file-list`, `.file-row`, etc.) for a file/module section instead of drawing the SVG module map.** This is the failure mode rule 6 exists to prevent. If you catch yourself reaching for a fresh class name to lay out filenames in a grid, stop and draw the boxes-and-arrows instead. The template stays rigid on purpose — channel inventive energy into the SVG itself, not into new component classes.
- **External fonts/CDN** — breaks double-click-to-open + offline use.
- **JavaScript for things CSS handles** — sticky positioning, `<details>` collapse, hover effects. Keep it static. Only reach for JS for genuine interactivity (sliders, drag-drop) and prefer not to.
- **Dropping content because a diagram supersedes it** — the prose still has to be there. The diagram is in addition to, not instead of.
- **Replacing or deleting the .md** — never.
- **Generic titles** — use the document's actual title; if missing, derive from filename.
- **Sidebar that doesn't link siblings** when converting multiple related files.
