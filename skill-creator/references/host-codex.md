# Codex adapter

How to install, configure, and surface skills in OpenAI Codex.

## Install paths

Codex scans these locations:

- **Personal**: `~/.codex/skills/<name>/`
- **Repo-local**: starting at cwd and walking up to repo root, every `.agents/skills/` directory is scanned
- **System**: `~/.codex/skills/.system/` (auto-installed by Codex; do not edit manually)

If the same skill name appears in multiple locations, Codex does **not** merge — both appear in skill selectors.

Codex follows symlinks during discovery, so the SSOT pattern works:

```txt
~/.codex/skills/<name>  →  ~/.skills/<name>
```

## Detection

Codex auto-detects changes. If a new skill doesn't appear, restart Codex.

To disable a skill without removing it, add to `~/.codex/config.toml`:

```toml
[[skills.config]]
path = "/path/to/skill/SKILL.md"
enabled = false
```

Restart Codex after editing the config.

## `agents/openai.yaml` schema

Optional file at `<skill>/agents/openai.yaml`. Configures three concerns: UI metadata, invocation policy, and tool dependencies. Codex reads it whenever the skill is loaded.

```yaml
interface:
  display_name: "User-facing name"
  short_description: "User-facing description"
  icon_small: "./assets/small-logo.svg"
  icon_large: "./assets/large-logo.png"
  brand_color: "#3B82F6"
  default_prompt: "Optional surrounding prompt to use the skill with"
policy:
  allow_implicit_invocation: false
dependencies:
  tools:
    - type: "mcp"
      value: "exampleMcpServer"
      description: "Example MCP server"
      transport: "streamable_http"
      url: "https://example.com/mcp"
```

### `interface`

UI-facing metadata for skill lists and chips in the Codex app. All fields optional. Include `icon_*` and `brand_color` only when explicitly provided — don't invent visuals. `default_prompt` populates the chip's default invocation text.

### `policy.allow_implicit_invocation`

Default: `true`. When `false`, Codex won't auto-invoke the skill based on description matching — only explicit `$skill-name` invocation works.

Set `false` for high-impact skills where deliberate invocation is preferred:

- Deploy / release workflows
- Database migrations
- Destructive file or repo operations
- Anything with side effects the user should consciously confirm

For normal skills (read-only analysis, formatting, refactoring helpers), leave it `true` so Codex can pick the skill up from description matching.

### `dependencies.tools`

Declares external dependencies — typically MCP servers — that the skill expects. Codex surfaces missing dependencies during install or activation.

Fields per tool entry:

- `type`: dependency type (e.g. `"mcp"`)
- `value`: identifier the host uses to reference the dependency
- `description`: human-readable label
- `transport`: connection type (e.g. `"streamable_http"`)
- `url`: endpoint

## Generating `openai.yaml`

OpenAI's reference skill-creator ships a generator script (`scripts/generate_openai_yaml.py` in the `openai/skills` repo):

```bash
scripts/generate_openai_yaml.py <path/to/skill-folder> --interface key=value
```

Derive `display_name`, `short_description`, and `default_prompt` from the `SKILL.md` description rather than rewriting from scratch — they should describe the same thing in slightly different framings (full description for triggering, short forms for the UI). On `SKILL.md` updates, regenerate to keep the adapter in sync.

## References

- [Codex skills documentation](https://developers.openai.com/codex/skills)
- [openai/skills repository](https://github.com/openai/skills) — `.system/skill-creator/references/openai_yaml.md` has field-level details
