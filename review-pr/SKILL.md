---
name: review-pr
version: 1.0.0
description: |
  Pre-landing PR review. Analyzes diff against the base branch for SQL safety, LLM trust
  boundary violations, race conditions, and other structural issues that tests don't catch.
  Language-agnostic — detects project language automatically and applies relevant patterns.
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Grep
  - Glob
  - AskUserQuestion
---

## Step 0: Detect base branch

Determine which branch this PR targets.

1. Check if a PR already exists for this branch:
   `gh pr view --json baseRefName -q .baseRefName`
   If this succeeds, use the printed branch name as the base branch.

2. If no PR exists (command fails), detect the repo's default branch:
   `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`

3. If both commands fail, fall back to `main`.

Print the detected base branch name. In every subsequent `git diff`, `git log`, and `git fetch` command, substitute the detected branch name wherever the instructions say "the base branch."

---

## Step 0.5: Detect project language(s)

Run the following to identify what kind of project this is:

```bash
ls package.json go.mod Cargo.toml pyproject.toml setup.py requirements.txt \
   Gemfile mix.exs pom.xml build.gradle 2>/dev/null
```

Record which files exist. Use this to activate language-specific checklist patterns in Step 4.
Multiple files may be present (e.g. a Python backend + JS frontend). Detect all of them.

Language → marker file mapping:
- **JavaScript / TypeScript**: `package.json`
- **Python**: `pyproject.toml`, `setup.py`, `requirements.txt`
- **Go**: `go.mod`
- **Rust**: `Cargo.toml`
- **Ruby**: `Gemfile`
- **Elixir**: `mix.exs`
- **Java / Kotlin**: `pom.xml`, `build.gradle`

Print: `Languages detected: [list]`

---

## Step 1: Check branch

1. Run `git branch --show-current` to get the current branch.
2. If on the base branch, output: **"Nothing to review — you're on the base branch or have no changes against it."** and stop.
3. Run `git fetch origin <base> --quiet && git diff origin/<base> --stat` to check if there's a diff. If no diff, output the same message and stop.

---

## Step 2: Read the checklist

Read `.claude/skills/review-pr/checklist.md`.

**If the file cannot be read, STOP and report the error.** Do not proceed without the checklist.

---

## Step 3: Get the diff

Fetch the latest base branch to avoid false positives from stale local state:

```bash
git fetch origin <base> --quiet
```

Run `git diff origin/<base>` to get the full diff. This includes both committed and uncommitted changes against the latest base branch.

---

## Step 4: Two-pass review

Apply the checklist against the diff in two passes:

1. **Pass 1 (CRITICAL):** SQL & Data Safety, Race Conditions & Concurrency, LLM Output Trust Boundary, Enum & Value Completeness
2. **Pass 2 (INFORMATIONAL):** Conditional Side Effects, Magic Numbers & String Coupling, Dead Code & Consistency, LLM Prompt Issues, Test Gaps, Crypto & Entropy, Time Window Safety, Type Coercion, View/Frontend

**Language-specific patterns:** For each category in the checklist, apply the patterns tagged with the detected language(s) from Step 0.5. Skip patterns tagged for other languages.

**Enum & Value Completeness requires reading code OUTSIDE the diff.** When the diff introduces a new enum value, status, or type constant, use Grep to find all files that reference sibling values, then Read those files to check if the new value is handled. This is the one category where within-diff review is insufficient.

Follow the output format specified in the checklist. Respect the suppressions — do NOT flag items listed in the "DO NOT flag" section.

---

## Step 4.5: Design Review (conditional)

Check if the diff touches frontend files:

```bash
git diff origin/<base> --name-only | grep -E '\.(css|scss|sass|less|html|jsx|tsx|svelte|vue)$'
```

**If no frontend files changed:** Skip design review silently. No output.

**If frontend files changed:**

1. Check for `DESIGN.md` or `design-system.md` in the repo root. If found, read it — patterns explicitly blessed there are NOT flagged. If not found, use universal design principles.

2. Read `.claude/skills/review-pr/design-checklist.md`. If not found, skip design review with a note.

3. Read each changed frontend file in full (not just diff hunks).

4. Apply the design checklist. Classify findings as:
   - **AUTO-FIX**: mechanical CSS fixes (`outline: none`, `!important`, `font-size < 16px`)
   - **ASK**: anything requiring design judgment
   - **POSSIBLE**: low-confidence findings — present as "Possible — verify visually"

Include design findings in the Step 5 Fix-First flow.

---

## Step 5: Fix-First Review

**Every finding gets action — not just critical ones.**

Output a summary header: `Pre-Landing Review: N issues (X critical, Y informational)`

### Step 5a: Classify each finding

For each finding, classify as AUTO-FIX or ASK per the Fix-First Heuristic in checklist.md.
Critical findings lean toward ASK; informational findings lean toward AUTO-FIX.

### Step 5b: Auto-fix all AUTO-FIX items

Apply each fix directly. For each one, output a one-line summary:
`[AUTO-FIXED] [file:line] Problem → what you did`

### Step 5c: Batch-ask about ASK items

If there are ASK items remaining, present them in ONE AskUserQuestion:

- List each item with a number, the severity label, the problem, and a recommended fix
- For each item, provide options: A) Fix as recommended, B) Skip
- Include an overall RECOMMENDATION

Example format:
```
I auto-fixed 3 issues. 2 need your input:

1. [CRITICAL] src/db/users.go:88 — Raw string interpolation in SQL query
   Fix: Use parameterized query with `?` placeholder
   → A) Fix  B) Skip

2. [INFORMATIONAL] src/api/handler.py:44 — LLM output written to DB without format validation
   Fix: Add regex check before persisting email field
   → A) Fix  B) Skip

RECOMMENDATION: Fix both — #1 is exploitable, #2 prevents silent data corruption.
```

If 3 or fewer ASK items, you may use individual AskUserQuestion calls instead of batching.

### Step 5d: Apply user-approved fixes

Apply fixes for items where the user chose "Fix." Output what was fixed.

If no ASK items exist (everything was AUTO-FIX), skip the question entirely.

---

## Step 5.5: TODOS cross-reference

Read `TODOS.md` in the repository root (if it exists). Cross-reference the PR against open TODOs:

- **Does this PR close any open TODOs?** If yes, note: "This PR addresses TODO: <title>"
- **Does this PR create work that should become a TODO?** If yes, flag as informational.
- **Are there related TODOs that provide context?** If yes, reference them when discussing related findings.

If `TODOS.md` doesn't exist, skip this step silently.

---

## Step 5.6: Documentation staleness check

For each `.md` file in the repo root (README.md, ARCHITECTURE.md, CONTRIBUTING.md, CLAUDE.md, etc.):

1. Check if code changes in the diff affect features or workflows described in that doc.
2. If the doc was NOT updated in this branch but the code it describes WAS changed, flag it as INFORMATIONAL:
   `"Documentation may be stale: [file] describes [feature] but code changed in this branch."`

This is informational only — never critical.

If no documentation files exist, skip this step silently.

---

## Important Rules

- **Read the FULL diff before commenting.** Do not flag issues already addressed in the diff.
- **Fix-first, not read-only.** AUTO-FIX items are applied directly. ASK items are only applied after user approval. Never commit, push, or create PRs.
- **Be terse.** One line problem, one line fix. No preamble.
- **Only flag real problems.** Skip anything that's fine.
- **Language patterns are additive.** If a pattern doesn't apply to the detected language, skip it silently. Don't explain what you're skipping.
