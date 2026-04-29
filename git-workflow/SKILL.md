---
name: git-workflow
description: Git staged changes review and commit message drafting. Use when asked to review staged changes, summarize a diff, write a commit message, or prepare to commit. Includes Conventional Commits format with automatic validation.
---

## Review Staged Changes

Run `git diff --staged` and summarize:
- What changed and why it matters
- Potential bugs, security, or performance issues

Be concise and developer-friendly.

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

**Scope**: Derive from changed files (e.g., `pw_cp.py` → `pw-cp`)

**Title**:
- **MUST be ≤49 characters** (hard limit)
  - Use agent to devise a concise title using commands: `echo -n "title" | wc -c`
- Use imperative mood ("fix", not "fixed")
- No trailing period
- **ALWAYS output: `Title: XX characters ✓`**

**Body**: 2-4 bullets explaining what/why
- **Do NOT wrap body lines** at 50-60 or 72 characters. Write each bullet as a single line regardless of length; let the terminal/viewer handle soft-wrapping.

### Output Structure

1. Brief change summary
2. Draft commit in code block
3. Character count validation

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

### Critical

If title >50 chars, provide shorter alternatives with counts.
Never skip the character count line.
