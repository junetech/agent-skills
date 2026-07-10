# md-to-html TODO

## Let the LLM look at the rendered page

`scripts/validate_output.py` is a pure text checker. Every invariant it enforces was
picked because it can be verified without rendering — no `<link>`, no `fetch(`, footer
present, heading anchors match. So the whole class of **"does it actually behave that
way on screen"** bugs is structurally out of reach.

A real case: the CSS-only tabs in `assets/components/tabs.html` used
`.mdh-tab-panel:target ~ .mdh-tab-panel:first-of-type`. The general-sibling combinator
only matches siblings *after* the target, so it never matched the first panel. Clicking
tab 2 showed panels 1 and 2 at once. The validator passed it; the bug surfaced only when
someone read the CSS closely during review.

### What we want

An eval stage that loads the generated HTML in a headless browser, drives it, and
asserts on the result.

- Approaches:
  - **Screenshot → vision.** Render to PNG and hand the image to the model. The only way
    to catch "the button is behind the modal" or "this contrast is unreadable." Tied to
    one viewport and one scroll position.
  - **Accessibility tree.** What Playwright-style MCP servers mostly use: a tree of
    roles, names, and states plus stable click handles. Cheap, post-layout, so it knows
    what is genuinely visible. Knows nothing about aesthetics.
  - In practice, combine them — drive with the a11y tree, screenshot only when a visual
    claim needs checking.

- Minimum scope to start with:
  - `document`: open the file, click tab 2, assert exactly one visible `.mdh-tab-panel`.
  - `deck`: press ArrowRight, assert one `.mdh-slide.active` and that its index advanced by one.
  - `editor`: flip a toggle, assert `#diff-out` textContent changed. With JS disabled,
    assert the data is visible in the static DOM (invariant 8 is only a soft warning
    today, so it needs a real measurement).
  - `sandbox`: move a slider, assert the preview style and the copy-params output both update.

- Open questions:
  - Where the harness lives — extend the assertions in `evals/evals.json`, or a separate runner.
  - How to handle the browser dependency. `validate_output.py` is standard-library only,
    and `git-workflow` holds the same line (python 3.7+, zero third-party packages).
    Pulling in Playwright would make this the one heavy skill. Probably belongs as an
    optional check that skips when no browser is available.
  - Output is a single file opened over `file://`, so no server is needed. Still need to
    decide how this composes with the existing flags like `--forbid-svg`.
