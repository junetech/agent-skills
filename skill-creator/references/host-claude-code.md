# Claude Code adapter

How to install, package, and distribute skills for Claude Code (and related Claude product surfaces).

## Install scopes

Four discovery locations, with conflict precedence:

| Scope | Path | Source |
| --- | --- | --- |
| Enterprise | (provisioned via MDM / admin policy) | IT push, highest priority |
| Personal | `~/.claude/skills/<name>/` | individual user, all projects |
| Project | `<repo-root>/.claude/skills/<name>/` | committed to repo, shared with team |
| Plugin | (installed via Anthropic Marketplace or plugin URL) | namespaced as `plugin-name:skill-name` |

Precedence on name clash: **enterprise > personal > project**. Plugin skills can't conflict — the `plugin-name:` prefix keeps them in their own namespace.

If a skill and a slash command (`.claude/commands/`) share a name, the skill wins.

Project skills are picked up from `.claude/skills/` in the starting directory **and every parent directory up to the repo root** — starting Claude Code in a subdirectory still finds skills defined at the root.

Claude Code follows symlinks during discovery, so the SSOT pattern works:

```txt
~/.claude/skills/<name>  →  ~/.skills/<name>
```

## Hot reload

Claude Code watches `~/.claude/skills/`, project `.claude/skills/`, and any `.claude/skills/` inside `--add-dir` directories. Adding, editing, or removing a skill takes effect within the current session.

**Exception**: creating a *new* top-level `.claude/skills/` directory that didn't exist when the session started requires restarting Claude Code so the new directory can be watched.

## `${CLAUDE_SKILL_DIR}` variable

Resolves at runtime to the skill's own directory, regardless of which scope it was installed under. Use it whenever bundled scripts or assets need to be referenced from outside the skill:

```bash
python3 ${CLAUDE_SKILL_DIR}/scripts/visualize.py .
```

Avoids hard-coding personal vs project vs plugin paths and keeps the skill portable across scopes.

## Subagent caveat

Task subagents do **not** automatically inherit the main conversation's skills. A subagent will not see the skill that triggered the parent task unless the skill is explicitly passed.

This matters for the eval-driven loop in `SKILL.md` — when spawning subagent runs to exercise a skill, include the skill path in the task prompt rather than assuming inheritance.

## Packaging (`.skill` archive)

Anthropic's `package_skill.py` (from the `anthropics/skills` repo) bundles a skill folder into a `.skill` file — a ZIP archive with a different extension.

```bash
python utils/package_skill.py <path/to/skill-folder> [output-directory]
```

Default exclude patterns:

- Directories anywhere in the tree: `__pycache__`, `node_modules`
- File globs anywhere: `*.pyc`
- Files anywhere: `.DS_Store`
- Directories at the skill root only: `evals/`

The script runs `quick_validate.py` before packaging — invalid skills aren't bundled.

`.skill` and `.zip` are interchangeable. Same underlying ZIP format, both extensions are accepted by most Claude tooling and third-party loaders.

When packaging, place `SKILL.md` either at the archive root or inside a single top-level directory (`<skill-name>/SKILL.md`). Either layout is valid; pick one and be consistent.

## claude.ai upload

For uploading custom skills to the claude.ai web app (Pro / Max / Team / Enterprise plans with code execution enabled):

1. Zip the skill folder (`.skill` or `.zip` extension both work)
2. Settings → Capabilities → enable **Code execution and file creation**
3. Settings → Customize → Skills → upload

Custom skills on claude.ai are per-user. They aren't shared org-wide and can't be centrally managed by admins (unlike Team/Enterprise provisioned skills, which are pushed by owners through organization settings).

## References

- [Claude Code skills documentation](https://code.claude.com/docs/en/skills)
- [Agent Skills (Claude API)](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)
- [anthropics/skills repository](https://github.com/anthropics/skills) — reference implementation including `package_skill.py` and `quick_validate.py`
