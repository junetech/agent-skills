# Host adapters

How to make a portable skill behave correctly on each agent host.

## When to read

Open this file when:

- Installing a skill on a new host for the first time
- The same skill behaves differently across hosts and you need to know why
- Adding host-specific concerns (UI metadata, invocation policy, packaging) that don't belong in `SKILL.md`

For host-specific details, see:

- [`host-codex.md`](host-codex.md) — Codex install paths, `agents/openai.yaml` schema, invocation policy, MCP dependencies
- [`host-claude-code.md`](host-claude-code.md) — Claude Code scopes, hot reload, `${CLAUDE_SKILL_DIR}`, packaging, subagent caveats
- [`host-opencode.md`](host-opencode.md) — opencode install paths, permission system, no hot reload, plugin vs skill distinction

## Cross-host SSOT pattern

Keep one source per skill and symlink into each host's discovery path:

```txt
~/.skills/<skill-name>/           ← single source
├── SKILL.md
├── scripts/
├── references/
└── agents/openai.yaml            (Codex-only adapter, lives in source)

~/.codex/skills/<skill-name>      → symlink → ~/.skills/<skill-name>
~/.claude/skills/<skill-name>     → symlink → ~/.skills/<skill-name>
~/.config/opencode/skills/<name>  → symlink → ~/.skills/<skill-name>
```

Codex, Claude Code, and opencode all follow symlinks during discovery, so the source is shared but each host sees the skill under its native path. Edit once, all hosts pick it up.

Host-specific adapter files live alongside `SKILL.md` in the source — only the host that uses them reads them, so they don't bleed across.

On Windows, symlink creation requires admin privileges (PowerShell) or Developer Mode enabled. Git Bash on Windows uses different symlink semantics from native Windows — verify before relying on shared scripts.

## The `compatibility` frontmatter field

The spec-standard way to declare host or environment requirements. Use it whenever the skill's correctness depends on a particular host or toolchain:

```yaml
compatibility: Designed for Claude Code (or similar products)
compatibility: Requires git, docker, jq
compatibility: Requires Python 3.14+ and uv
```

Prefer this over baking host names into the body of `SKILL.md`. Anything the *agent* should know about runtime environment goes here; anything host-specific the agent doesn't need (UI metadata, packaging artifacts) goes into adapter files.

## Adding a new host

When extending support to a new host, work through this checklist:

1. **Install path** — Where does the host discover skills? Home directory, repo-local, both?
2. **Symlink support** — Does the host follow symlinks during discovery?
3. **Required adapter files** — Does the host need extra metadata (UI fields, invocation policy, dependencies)?
4. **Packaging format** — Single folder, ZIP archive (`.skill` / `.zip`), or other?
5. **Detection** — Hot reload, or restart required?
6. **`compatibility` field** — Does the host read the spec's `compatibility` field and surface it to the user?
7. **Subagent behavior** — Do spawned subagents inherit skills automatically, or must they be passed explicitly?

Document findings in a new `references/host-<name>.md` and add a pointer to the list above.
