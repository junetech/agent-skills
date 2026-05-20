# opencode adapter

How to install, configure, and surface skills in opencode.

## Install paths

opencode scans six locations, covering both its native layout and compatibility paths from other hosts:

| Scope | Path | Source |
| --- | --- | --- |
| Project (native) | `.opencode/skills/<name>/SKILL.md` | opencode-specific, repo-local |
| Global (native) | `~/.config/opencode/skills/<name>/SKILL.md` | individual user, all projects |
| Project (Claude) | `.claude/skills/<name>/SKILL.md` | Claude Code compatible |
| Global (Claude) | `~/.claude/skills/<name>/SKILL.md` | Claude Code compatible |
| Project (agent) | `.agents/skills/<name>/SKILL.md` | agent-generic compatible |
| Global (agent) | `~/.agents/skills/<name>/SKILL.md` | agent-generic compatible |
| System | `~/.codex/skills/.system/<name>/SKILL.md` | auto-installed; do not edit manually |

For project-local paths, opencode walks up from cwd to the git worktree root — starting in a subdirectory still finds skills defined at the repo root.

If the same skill name appears in multiple locations, opencode does **not** merge — all instances appear in skill selectors.

opencode follows symlinks during discovery, so the SSOT pattern works:

```txt
~/.config/opencode/skills/<name>  →  ~/.skills/<name>
~/.claude/skills/<name>           →  ~/.skills/<name>
```

The `CODEX_HOME` environment variable overrides `~/.codex` as the base path for system skills.

## Detection

opencode loads configuration and skills **once at startup**. There is no hot reload.

After adding, editing, or removing a skill, the user must quit and restart opencode. Use `opencode debug skill` to verify the current skill list after restart.

## Permission system

opencode has a per-skill permission model. In `opencode.json`:

```json
{
  "permission": {
    "skill": {
      "*": "allow",
      "internal-*": "deny",
      "experimental-*": "ask"
    }
  }
}
```

Three permission levels:

| Level | Behavior |
| --- | --- |
| `allow` | Skill loads immediately when triggered |
| `deny` | Skill is hidden from the agent entirely |
| `ask` | User is prompted before the skill loads |

Glob patterns match against skill names. More specific patterns take precedence.

### Per-agent overrides

Custom agents can override skill permissions in their frontmatter:

```yaml
---
permission:
  skill:
    "documents-*": "allow"
---
```

Built-in agents (`plan`, `build`, `general`, `explore`) are configured in `opencode.json`:

```json
{
  "agent": {
    "plan": {
      "permission": {
        "skill": { "internal-*": "allow" }
      }
    }
  }
}
```

### Disabling the skill tool entirely

To prevent an agent from using any skill:

- Custom agent: `tools: { skill: false }` in frontmatter
- Built-in agent: `"tools": { "skill": false }` in `opencode.json`

## `agents/openai.yaml`

opencode reads `agents/openai.yaml` the same way Codex does — the schema, fields, and behavior are identical. See [`host-codex.md`](host-codex.md) for the full schema reference.

Brief summary:

```yaml
interface:
  display_name: "User-facing name"
  short_description: "User-facing description"
  brand_color: "#3B82F6"
  default_prompt: "Optional default invocation text"
policy:
  allow_implicit_invocation: true
dependencies:
  tools: []
```

opencode does **not** have its own UI metadata format — reuse the Codex adapter file.

## Plugin system (vs skills)

opencode has a separate plugin system alongside skills. They are not interchangeable:

| Aspect | Skills | Plugins |
| --- | --- | --- |
| Format | `SKILL.md` folder | npm module with `plugin.json` manifest |
| Loading | On-demand via `skill` tool | At startup, always active |
| Install | Copy folder to skill path | `opencode plugin <npm-module>` |
| Capabilities | Instructions only | Hooks, custom tools, events, provider registration |
| Config | Frontmatter only | `opencode.json` `plugin` field |

Plugins can register custom tools, intercept events, modify system prompts, and more via the `@opencode-ai/plugin` SDK. Skills are purely instruction-based.

Plugin locations:
- `.opencode/plugins/` — project-level
- `~/.config/opencode/plugins/` — global

## Debug commands

| Command | Purpose |
| --- | --- |
| `opencode debug skill` | List all discovered skills with name, description, location |
| `opencode debug config` | Show resolved configuration |
| `opencode debug paths` | Show global paths (data, config, cache, state) |
| `opencode debug agent <name>` | Show agent configuration details |
| `opencode debug info` | Show version, OS, terminal, plugins |

## References

- [opencode documentation](https://opencode.ai)
- [opencode config schema](https://opencode.ai/config.json)
- [Agent Skills specification](https://agentskills.io/specification)
