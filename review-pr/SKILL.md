---
name: review-pr
description: |
  Read-only pre-landing PR or branch review against its base branch. Use when the user
  wants to review a pull request, audit a branch diff before pushing or merging, or asks
  "review my PR", "review this branch", "check before I merge", or similar. Only modify
  files when the user explicitly asks to fix, apply, address, or otherwise implement
  review findings. Scans for SQL injection and data-safety issues, races and TOCTOU,
  LLM output trust-boundary violations, enum/state completeness, magic numbers, dead
  code, crypto weaknesses, time-window bugs, type coercion, and frontend/design
  anti-patterns. Language-agnostic. Not for commit-message drafting or staged-only
  commit review (use git-workflow), nor for arbitrary code outside a branch diff.
compatibility: Requires git. The gh CLI is optional and improves pull-request base detection.
---

## Step 0: Select the operating mode

Default to **REVIEW mode**, which is read-only. A request to review, audit, inspect, or
check a PR or branch does not authorize file edits.

Enter **FIX mode** only when the user explicitly asks to fix, apply, address, implement,
or otherwise change review findings. The permission covers those fixes only; never
commit, push, open a PR, or make unrelated changes.

Print `Mode: REVIEW (read-only)` or `Mode: FIX (edits authorized)`.

## Step 1: Resolve the base branch and comparison ref

Resolve the intended target without assuming `origin` exists and without silently
falling back to `main`.

1. Record the current branch with `git branch --show-current`. Detached HEAD is allowed.
2. If `gh` is available, run `gh pr view --json baseRefName -q .baseRefName`. If it
   succeeds, use that base branch name.
3. Identify a remote independently of `gh`:
   - Prefer the current branch's configured upstream remote.
   - Otherwise prefer `origin` if it exists.
   - Otherwise use the only configured remote if exactly one exists.
   - If there are several remaining remotes, do not guess.
4. If the base branch is still unknown and a remote was selected, resolve its default
   branch from `refs/remotes/<remote>/HEAD` with `git symbolic-ref`. If that ref is
   absent, try `git ls-remote --symref <remote> HEAD`; network failure is non-fatal.
5. If the base is still unknown, inspect `init.defaultBranch` and existing local refs
   among `main`, `master`, `trunk`, and `develop`. Use a candidate only when it identifies
   one unambiguous existing branch.
6. If the base is still unknown or candidates conflict, ask the user for the base branch
   and wait. Never choose `main` merely because detection failed.
7. Resolve `<base-ref>` to an actual ref:
   - With a selected remote, fetch only the base branch. Prefer the updated
     `<remote>/<base>` ref; if fetch fails, report that the remote ref may be stale.
   - Without a usable remote ref, use the local `<base>` branch if it exists.
   - If neither ref exists, report the missing ref and ask the user how to proceed.

Print `Base: <branch> (<base-ref>)`. Use `<base-ref>` in every later comparison.

## Step 2: Detect project languages

Inspect repository marker files and activate every applicable language:

- JavaScript / TypeScript: `package.json`
- Python: `pyproject.toml`, `setup.py`, `requirements.txt`
- Go: `go.mod`
- Rust: `Cargo.toml`
- Ruby: `Gemfile`
- Elixir: `mix.exs`
- Java / Kotlin: `pom.xml`, `build.gradle`

Print `Languages detected: [list]`.

## Step 3: Build the complete review set

Treat the review set as four explicit, non-overlapping sources:

1. Committed branch changes: `git diff <base-ref>...HEAD`
2. Staged changes relative to HEAD: `git diff --cached`
3. Unstaged tracked changes: `git diff`
4. Untracked, non-ignored files: `git ls-files --others --exclude-standard`

Read every diff in full before reporting findings. Read each reviewable untracked text
file in full as well. For a binary or impractically large untracked file, inspect its
type and size, state how it was handled, and do not silently omit it.

Build one de-duplicated changed-file list from the four sources. Use that same list for
language checks, frontend detection, TODO cross-references, and documentation staleness.
Only output `Nothing to review — no committed, staged, unstaged, or untracked changes
against <base-ref>.` and stop when all four sources are empty. Being on the base branch
alone is not a reason to stop when local changes exist.

## Step 4: Read the checklists

Read `checklist.md`. If it cannot be read, stop and report the error; do not review
without it.

If the changed-file list contains `.css`, `.scss`, `.sass`, `.less`, `.html`, `.jsx`,
`.tsx`, `.svelte`, or `.vue`, also:

1. Read root `DESIGN.md` or `design-system.md` when present; documented project choices
   override generic design heuristics.
2. Read `design-checklist.md`. If unavailable, continue the code review and report that
   the design pass was skipped.
3. Read every changed frontend file in full, including untracked frontend files.

Skip the design pass silently when no frontend file changed.

## Step 5: Perform the two-pass review

Apply `checklist.md` to the complete review set:

1. **CRITICAL:** SQL & Data Safety, Race Conditions & Concurrency, LLM Output Trust
   Boundary, Enum & Value Completeness
2. **INFORMATIONAL:** every remaining category

Apply only language-specific patterns matching the detected languages. Enum and value
completeness requires searching outside the diff for every consumer of sibling values,
then reading each relevant match.

For frontend changes, apply `design-checklist.md`. Respect all suppressions and do not
flag anything already handled elsewhere in the complete review set.

Give every finding two independent labels:

- Severity: `CRITICAL` or `INFORMATIONAL`.
- Disposition: `FIX` for an unambiguous mechanical change, or `ASK` when judgment is
  required. Low-confidence `POSSIBLE` design findings are confidence annotations, not a
  third disposition; classify all of them as `ASK`.

## Step 6: Report or fix findings

Follow the output contract in `checklist.md`.

### REVIEW mode

Do not edit files. Report `FIX` findings as suggested mechanical fixes and `ASK`
findings as decisions or verification the user must make. Make the report sufficient
for a later explicit fix request.

### FIX mode

1. Apply all `FIX` findings and report each changed `file:line` with a terse summary.
2. Batch every `ASK` finding into one user prompt. Use the host's normal user-input
   facility when available. Otherwise print one numbered plain-text question with
   `Fix as recommended` and `Skip` choices, then wait for the reply.
3. If the execution environment cannot collect a reply, leave `ASK` items unchanged and
   report them clearly.
4. Apply only the fixes the user approves. Never infer approval from the original review
   request.

## Step 7: Cross-check TODO list and documentation

If root `TODO.md` exists, note open items the branch closes, work it creates, and related
context. Skip silently when absent.

For each root Markdown document, check whether the reviewed code changes behavior or a
workflow it describes. If that document was not updated in the review set, report an
INFORMATIONAL finding: `Documentation may be stale: [file] describes [feature] but code
changed in this branch.`

## Important rules

- Read the complete review set before commenting.
- Remain read-only unless the user explicitly requested fixes.
- Never commit, push, or create a PR.
- Be terse: one line for the problem and one for the recommended or applied fix.
- Flag only real problems. Skip anything already addressed in the review set.
- Apply language patterns additively and skip irrelevant patterns silently.
