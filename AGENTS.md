# Repository Guidance

## `vault/plans/`

- Use `vault/plans/` for implementation plans that should survive context resets or be handed to another agent.
- Store plans as Markdown files named `yyyymmdd_descriptive_snake_case.md`, all lowercase, for example `20260528_md_to_spatial_html_skill_improvement.md`.
- A plan should include the goal, key changes, test plan, assumptions, and enough file/interface detail for another agent to implement without rediscovering decisions.
- Treat plan files as planning artifacts, not executable specs. When implementation changes from the plan, update the plan only if the plan remains useful as project memory.
