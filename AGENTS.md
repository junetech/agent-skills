# Repository Guidance

## `vault/plans/`

- Use `vault/plans/` for implementation plans that should survive context resets or be handed to another agent.
- Store plans as Markdown files named `yyyymmdd_descriptive_snake_case.md`, all lowercase, for example `20260528_md_to_spatial_html_skill_improvement.md`.
- A plan should include the goal, key changes, test plan, assumptions, and enough file/interface detail for another agent to implement without rediscovering decisions.
- Treat plan files as planning artifacts, not executable specs. When implementation changes from the plan, update the plan only if the plan remains useful as project memory.

## `skills-ref/` — Skill validation/management CLI tool

[reference](https://github.com/agentskills/agentskills/tree/main/skills-ref)

**Requirements:** [uv](https://docs.astral.sh/uv/) must be installed on the system.

- **This repo's internal tool only.** Not meant for external projects — only for validating and managing skill directories under `agent-skills/`.
- `skills-ref/` is a standalone Python package (has its own `pyproject.toml`, `uv.lock`). **No need to `uv init` at the repo root.**
- **One-time setup:** run `uv sync` inside `skills-ref/`.

  ```sh
  cd skills-ref
  uv sync
  ```

- **Usage:** always from the **repo root** with `--directory` flag.
  - `uv run --directory skills-ref skills-ref validate ../<skill-dir>` — validate a skill
  - `uv run --directory skills-ref skills-ref read-properties ../<skill-dir>` — print properties as JSON
  - `uv run --directory skills-ref skills-ref to-prompt ../<skill-dir> ...` — generate `<available_skills>` XML
  > Note: `--directory skills-ref` changes the working directory to `skills-ref/`, so paths are relative to that directory (hence the `../` prefix).
- **Examples:**

  ```sh
  uv run --directory skills-ref skills-ref validate ../git-workflow/
  uv run --directory skills-ref skills-ref to-prompt ../git-workflow/ ../review-pr/
  ```

- Run `validate` right after creating or modifying a skill to ensure it conforms to the spec.
