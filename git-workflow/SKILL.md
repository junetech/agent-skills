---
name: git-workflow
description: Git staged changes review and commit message drafting. Use when asked to review staged changes, summarize a diff, write a commit message, or prepare to commit. Uses Conventional Commits format with a title length check (≤49 chars).
compatibility: Tested on Claude Code with Git Bash (MINGW64) on Windows/Linux. Untested on macOS.
---

## Review Staged Changes

Run `git diff --staged` and summarize:
- What changed and why it matters
- Potential issues, classified as:
  - **Critical**: data loss, security vulnerability, broken build, exposed secret, incorrect business logic
  - **Warning**: style, minor performance, unclear naming, missing test

Be concise and developer-friendly.

### When the user also asks for a commit message

- **Critical issues present** → halt. Do not draft a commit message. Report findings and wait for direction; drafting a message here would invite the user to commit a broken change.
- **Only warnings (or no issues)** → proceed to "Draft Commit Message" and list warnings alongside the draft.

## Draft Commit Message

Run `git diff --staged`, then draft a Conventional Commits message:

```
<type>(<scope>): <summary>

- Bullet 1
- Bullet 2
```

### Rules

**Type** (choose one):
- `feat` - new feature
- `fix` - bug fix
- `refactor` - restructuring
- `docs` - documentation
- `perf` - performance
- `test` - tests
- `chore` - maintenance

**Breaking change**: append `!` after the type/scope (e.g., `feat(api)!: drop legacy endpoint`).

**Scope**: Derive from changed files (e.g., `pw_cp.py` → `pw-cp`)

**Title**:
- ≤49 characters, hard limit (including the `<type>(<scope>): ` prefix)
  - Follows the 50-char title convention from [Tim Pope (2008)](https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html), with a 1-char safety margin so it never wraps in `git log --oneline`
  - Verify with `echo -n "title" | wc -c` (works in Git Bash / MINGW64)
- Use imperative mood ("fix", not "fixed")
- No trailing period
- Output `Title: XX characters ✓` after the draft; the user reads this line to confirm the limit was respected

**Body**: 2-4 bullets explaining what/why
- Write each bullet as a single line; do not hard-wrap at 50/60/72 chars. Modern terminals and viewers handle soft-wrapping themselves.

### Output Structure

- Review-only request → change summary
- Commit-message request → draft in code block + `Title: XX characters ✓`
- Both → summary, then (only if no critical issues) draft + count

### Examples

```
refactor(pw-cp): simplify batch logic

- Remove is_last_batch flag
- Consolidate solve paths
```

```
fix(schedule): handle None times

- Add null check before rendering
- Skip incomplete operations
```

### Title too long

If the title exceeds 49 characters, provide 2–3 shorter alternatives with character counts. The count line is part of the output contract; without it the user cannot verify the limit was respected.
