---
name: git-workflow
description: Git staged changes review and commit message drafting. Use when asked to review staged changes, summarize a diff, write a commit message, or prepare to commit. Uses Conventional Commits format with a title width check (≤49 display columns, so each CJK character counts as two).
compatibility: Requires python 3.7+ on PATH; one Python implementation, no shell mirror. Verified on Python 3.14 under Claude Code with Git Bash and under opencode with PowerShell, both on Windows with a cp949 locale; and on Python 3.12 under Linux with a C locale. Untested on macOS.
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
- ≤49 display columns, hard limit (including the `<type>(<scope>): ` prefix)
  - Follows the 50-char title convention from [Tim Pope (2008)](https://tbaggery.com/2008/04/19/a-note-about-git-commit-messages.html), with a 1-char safety margin so it never wraps in `git log --oneline`
  - Why columns and not bytes/chars: `wc -c` counts bytes, tripling a Korean title; a character count halves one, since East Asian Wide and Fullwidth code points occupy two columns each
  - Never count the title yourself. Run the bundled checker, passing every candidate in one call:

    ```sh
    # Linux / macOS
    python3 <skill-dir>/scripts/check_commit_msg.py '<title>' ['<title>' ...]
    # Windows
    python <skill-dir>/scripts/check_commit_msg.py '<title>' ['<title>' ...]
    ```

    `<skill-dir>` is this skill's own directory, which the harness reports when it loads the skill. A repo-relative path such as `git-workflow/scripts/...` resolves only inside this repo; the skill is installed outside the repo it runs in. Use the interpreter named for the current platform: on Linux `python` is often absent or aliased to Python 2, while on Windows `python` is the name the installer puts on PATH.
  - The checker prints one `Title: NN columns ✓` line per candidate — or `✗` plus one line per broken rule — and exits 0 when all pass, 1 otherwise
- Use imperative mood ("fix", not "fixed")
- No trailing period
- Paste the checker's `Title: NN columns ✓` line verbatim after the draft; the user reads this line to confirm the limit was respected

**Body**: 2-4 bullets explaining what/why
- Write each bullet as a single line; do not hard-wrap at 50/60/72 chars. Modern terminals and viewers handle soft-wrapping themselves.

### Output Structure

- Review-only request → change summary
- Commit-message request → draft in code block + `Title: NN columns ✓`
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

If the title exceeds 49 display columns, provide 2–3 shorter alternatives and pass them all to the checker in one call to print their column counts. The count line is part of the output contract; without it the user cannot verify the limit was respected.
