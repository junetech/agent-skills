---
name: skill-creator
description: Guide for creating new skills and iteratively improving existing ones. Use this whenever the user wants to create a skill from scratch, edit an existing skill, refine a skill's description for better triggering, or run test cases against a skill. Applies when the user mentions "skill", "SKILL.md", capturing a reusable workflow, or extending an agent's capabilities with specialized knowledge.
---

# Skill Creator

A skill for creating new skills and iteratively improving them, independent of which agent (Claude, Codex, or another LLM-based assistant) will load them.

## About Skills

Skills are modular, self-contained folders that extend an agent's capabilities with specialized knowledge, workflows, and tools. Think of them as onboarding guides for specific domains — they convert a general-purpose agent into a specialist equipped with procedural knowledge the base model does not possess.

The format follows the [Agent Skills specification](https://agentskills.io/specification), an open standard supported across multiple agent hosts (Claude Code, Codex, and others). Treat the spec as the ground truth when host-specific docs disagree.

What skills typically provide:

1. Specialized workflows — multi-step procedures for a specific domain
2. Tool integrations — instructions for working with specific file formats, APIs, or CLIs
3. Domain expertise — schemas, business logic, conventions
4. Bundled resources — scripts, references, and assets for repeated tasks

## Anatomy of a Skill

```
skill-name/
├── SKILL.md              (required)
│   ├── YAML frontmatter  (name, description — required)
│   └── Markdown body     (instructions)
└── Bundled resources     (optional)
    ├── scripts/          executable code for deterministic / repetitive tasks
    ├── references/       docs loaded into context on demand
    └── assets/           files used in the agent's output (templates, fonts, icons)
```

Frontmatter fields per the spec — two required, four optional:

**Required**

- `name`: the skill identifier. 1–64 characters, lowercase letters / digits / hyphens. Must not start or end with a hyphen, must not contain consecutive hyphens (`--`), and must match the parent directory name exactly. Prefer short verb-led phrases; namespace by tool when it aids triggering (`gh-address-comments`, `linear-create-issue`).
- `description`: the single primary triggering signal. ≤1024 characters, non-empty. Cover both *what* the skill does and *when* to use it — see "The description field" below.

**Optional**

- `license`: license name, or reference to a bundled `LICENSE.txt`.
- `compatibility`: ≤500 characters. Declares environment requirements — intended product, system packages, network access. Most skills don't need this. Examples: `compatibility: Designed for Claude Code (or similar products)` / `compatibility: Requires git, docker, jq`.
- `metadata`: arbitrary key-value map for extensions outside the spec. Use reasonably unique keys to avoid collisions.
- `allowed-tools`: space-separated string of pre-approved tools (experimental, support varies by host). Example: `allowed-tools: Bash(git:*) Bash(jq:*) Read`.

Do not add fields outside this set. Host-specific UI metadata (e.g. Codex's `agents/openai.yaml`) belongs in adapter files, not in frontmatter.

## Core Principles

### Context is a public good

The context window is shared between the system prompt, conversation history, every other skill's metadata, and the user's request. Every sentence in `SKILL.md` competes for that space. The default assumption is that the agent is already smart — only add what it does not already know. Challenge each paragraph: does it justify its token cost?

### Set appropriate degrees of freedom

Match the level of specificity to how fragile and variable the task is:

- **High freedom** (text-based instructions): multiple approaches valid, decisions depend on context, heuristics guide.
- **Medium freedom** (pseudocode, parameterized scripts): preferred pattern exists, some variation acceptable.
- **Low freedom** (specific scripts, few parameters): operations are fragile, consistency critical, sequence must be exact.

Picture the agent walking a path: a narrow bridge over a cliff needs guardrails (low freedom); an open field allows many routes (high freedom).

### Progressive disclosure

Skills use a three-level loading model:

1. **Metadata** (name + description) — always in context. ~100 tokens.
2. **SKILL.md body** — loaded only when the skill triggers. Keep under ~500 lines / ~5000 tokens.
3. **Bundled resources** — loaded as needed; scripts may execute without loading their source into context.

When `SKILL.md` approaches 500 lines, factor variant- or domain-specific details into `references/` and link them with clear "read this when…" pointers. For files over ~300 lines, include a table of contents at the top so the agent can preview scope without reading the whole file.

**Domain organization** — when a skill spans multiple variants, organize by variant so only the relevant reference is loaded:

```
cloud-deploy/
├── SKILL.md          (workflow + provider selection)
└── references/
    ├── aws.md
    ├── gcp.md
    └── azure.md
```

### Principle of lack of surprise

Skills must not contain malware, exfiltration logic, or anything whose effect would surprise the user given the skill's stated purpose. Roleplay and persona skills are fine; covertly malicious skills are not.

## Skill Creation Process

Six steps, in order, skipping only when a step is clearly inapplicable:

1. Capture intent
2. Plan reusable contents
3. Scaffold the skill folder
4. Write the skill
5. Validate
6. Iterate

### Step 1: Capture intent

Understand what the skill should do before writing anything. If the user said "turn this into a skill", extract structure from the conversation history first — the tools used, the sequence of steps, the corrections, the input/output formats — and only ask the user to fill the gaps.

Useful questions:

1. What should this skill enable the agent to do? Concrete examples?
2. When should it trigger — what user phrases or contexts?
3. What output format is expected?
4. Should test cases be set up? Skills with objectively verifiable outputs (file transforms, data extraction, code generation, fixed workflows) benefit from tests. Skills with subjective outputs (writing style, design) usually do not.

Do not ask all questions in one message. Start with the most decisive ones and follow up. Conclude this step only when the supported functionality is clear.

### Step 2: Plan reusable contents

Walk through each concrete example and ask:

1. How would I execute this from scratch?
2. What would be worth bundling so the next invocation does not repeat work?

Mapping examples:

- *"Help me rotate this PDF"* → bundle `scripts/rotate_pdf.py` (re-writing the same code each time is waste).
- *"Build me a todo app"* → bundle `assets/hello-world/` template (boilerplate is reused verbatim).
- *"How many users logged in today?"* → bundle `references/schema.md` (schemas have to be re-discovered every call).

Produce a list of `scripts/`, `references/`, and `assets/` items the skill needs.

### Step 3: Scaffold the skill folder

Create the folder named exactly after the skill (`skill-name/`), the empty `SKILL.md` with frontmatter, and any subdirectories planned in Step 2. If a scaffolding script is available in your environment (e.g. an `init_skill.py` helper), use it; otherwise create the structure with `mkdir`/`touch`.

Do not create directories you will not use. Do not create README.md, INSTALLATION.md, CHANGELOG.md, or other meta-files — see "What not to include" below.

### Step 4: Write the skill

This is the substantive step. Implement bundled resources first, then write `SKILL.md` last so the prose can reference real files.

#### Implement bundled resources first

Build out `scripts/`, `references/`, `assets/` based on Step 2's plan. Test scripts by running them — bundled code that crashes is worse than no script. If many scripts are similar, test a representative sample.

User input may be required here (brand assets, schema docs, templates).

#### Write SKILL.md

Frontmatter: `name` and `description`. See "The description field" below for the description's structure.

Body: instructions for using the skill and its bundled resources. Always use imperative form. Apply the writing guidelines below.

### Step 5: Validate

Run the reference validator from the Agent Skills project:

```bash
skills-ref validate ./skill-name
```

This checks YAML frontmatter format, required fields, the full set of name constraints (lowercase / hyphens / parent-dir match / no consecutive hyphens), description length, and that no unexpected fields are present.

If `skills-ref` isn't installed in the environment, fall back to a manual checklist:

- YAML frontmatter parses and contains `name` and `description`.
- `name` follows all naming rules (≤64 chars, hyphen-case, no leading/trailing/consecutive hyphens) and matches the folder name.
- `description` is non-empty and ≤1024 characters.
- No frontmatter fields outside the spec (`name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`).
- Every script referenced in `SKILL.md` exists at the cited path.
- Every reference file mentioned has a clear "when to read this" pointer.

### Step 6: Iterate

After the skill is usable, exercise it. See "Iteration loop" below.

## The description field

The description is the primary mechanism by which the agent decides whether to consult the skill. It must include both *what the skill does* and *when to use it* — every "when to use" cue belongs in the description, not in the body, because the body is loaded only after the skill has already triggered.

Two failure modes to watch for:

- **Undertriggering**: the skill exists but the agent does not consult it on relevant tasks. Combat this by enumerating concrete trigger phrases, file types, and adjacent tasks in the description.
- **Overtriggering**: the skill fires on near-miss queries that need something else. Combat this by being specific about what the skill is *not* for when the boundary is fuzzy.

Example (a `docx` skill):

> Comprehensive document creation, editing, and analysis with support for tracked changes, comments, formatting preservation, and text extraction. Use whenever the user needs to work with professional documents (.docx files), including: (1) creating new documents, (2) modifying or editing content, (3) working with tracked changes, (4) adding comments, or any other Word-document task.

Most agents lean toward undertriggering, so favor the more comprehensive description over the more minimal one.

## Writing guidelines

**Use imperative form.** "Run the script", not "the agent should run the script".

**Explain the *why*, not just the *what*.** Modern LLMs have good theory of mind and follow reasoning better than rote rules. A paragraph explaining *why* a step matters generalizes to cases the author did not enumerate; a paragraph of `ALWAYS`/`NEVER` directives does not. If the draft is full of all-caps mandates and rigid templates, reframe — that is a yellow flag.

**Examples over explanations.** A concise input/output pair often replaces several paragraphs of prose.

**Define output formats explicitly when they matter.**

```markdown
## Report structure
Use this exact template:
# [Title]
## Executive summary
## Key findings
## Recommendations
```

**Generalize.** The skill will be invoked across many prompts, not the three the author had in mind. Avoid overfitting instructions to specific examples.

**Draft, then revise with fresh eyes.** First passes are usually too long.

## What not to include

A skill should contain only files that directly serve its function. Do not create:

- README.md
- INSTALLATION_GUIDE.md
- QUICK_REFERENCE.md
- CHANGELOG.md
- Notes about the skill's development process

The skill is for an agent to do a job. It is not user-facing documentation. Auxiliary files dilute the signal in `SKILL.md` and add review burden.

## Iteration loop

Iteration is the heart of skill development. The level of rigor depends on what the host environment supports.

### Basic loop (always available)

1. Run the skill on 2–3 realistic test prompts — the kind of thing a real user would actually type.
2. Inspect outputs with the user. Note where the skill struggled or wasted effort.
3. Generalize the feedback. The skill must work for cases beyond these prompts; avoid overfitting fixes to the specific examples.
4. Revise `SKILL.md` or bundled resources.
5. Rerun and compare.

Keep going until the user is satisfied, the feedback is all empty, or progress stalls.

### Eval-driven loop (when the environment supports it)

If the host supports spawning independent runs (subagents, parallel sessions, CI invocations), upgrade the loop:

1. Write test prompts to `evals/evals.json` with an `id`, `prompt`, `expected_output`, and any input `files`.
2. For each prompt, run two configurations in parallel — *with* the skill and a *baseline* (no skill for new skills; the previous version for updates).
3. Capture timing and token counts as the runs complete.
4. Grade outputs against assertions (objective checks) or qualitatively (subjective outputs).
5. Aggregate into a benchmark with pass rates, time, tokens, and deltas per configuration.
6. Review with the user before revising.

When designing assertions, prefer objectively verifiable checks with descriptive names — they should read clearly in any results viewer.

### What to look for when improving

- **Repeated work across runs** — if every test case independently wrote a similar helper script, that script belongs in `scripts/`.
- **Wasted steps** — if the agent spent time doing something unproductive, identify the instruction that caused it and remove or reframe.
- **Overfitting** — if a fix only helps one of the test cases, it probably hurts others. Look for a more general framing.
- **Heavy-handed rules** — `ALWAYS X` and `NEVER Y` rarely solve real problems. Reframe by explaining the underlying reason.

### Description optimization

After the skill's content is stable, optimize the description for triggering. Generate ~20 eval queries — roughly half *should-trigger*, half *should-not-trigger*. The should-not-trigger queries are the valuable ones: aim for near-misses that share keywords or concepts with the skill but actually need something else. Obviously irrelevant queries ("write a fibonacci function" as a negative for a PDF skill) test nothing.

Realistic queries beat abstract ones — include file paths, column names, personal context, typos, casual phrasing, mixed lengths. Then either review with the user manually or run an automated description-rewriting loop if the environment supports it (described in `references/description-optimization.md` if bundled).

## Naming conventions

These constraints come from the spec and are enforced by `skills-ref validate`:

- Lowercase letters, digits, hyphens only. 1–64 characters.
- Must not start or end with a hyphen.
- Must not contain consecutive hyphens (`--`).
- Must match the parent directory name exactly.
- Short, verb-led phrases describe the action best.
- Namespace by tool when it improves clarity (`gh-address-comments`, `linear-create-issue`).

## Host-specific adapters

Skill content is portable, but a few surface concerns differ across hosts:

- **`compatibility` frontmatter field** — the spec-standard way to declare host or environment requirements. Use it whenever the skill's correctness depends on a particular host or toolchain. Examples: `compatibility: Designed for Claude Code (or similar products)`, `compatibility: Requires git, docker, jq`, `compatibility: Requires Python 3.14+ and uv`. Prefer this over baking host names into the prose.
- **UI metadata** — some hosts surface skills in a UI and need extra metadata (e.g. Codex reads `agents/openai.yaml` with `display_name`, `short_description`, `default_prompt`). Treat these as host-specific adapter files, generated from the same `SKILL.md` source rather than hand-maintained.
- **Subagents / parallel runs** — the eval-driven loop assumes the host can spawn independent runs. If it cannot, fall back to the basic loop.
- **Packaging** — some hosts install skills from `.skill` archives, others from a folder. The packaging step (if any) belongs in a per-host script, not in `SKILL.md`.

Keep `SKILL.md` host-neutral. Push host-specific concerns into adapter scripts, per-host reference files, or the `compatibility` field.

## Reference files

If the skill needs more depth than fits in this body, common reference files to add:

- `references/schemas.md` — JSON structures for evals, grading results, benchmarks
- `references/description-optimization.md` — detailed description rewriting workflow
- `references/host-adapters.md` — cross-host SSOT pattern, `compatibility` field usage, new-host checklist
- `references/host-codex.md` — Codex install paths, `agents/openai.yaml` schema, invocation policy, MCP dependencies
- `references/host-claude-code.md` — Claude Code scopes, hot reload, `${CLAUDE_SKILL_DIR}`, packaging, subagent caveats
- `references/host-opencode.md` — opencode install paths, permission system, no hot reload, plugin vs skill distinction

## External references

**Spec & official guides**

- [Agent Skills specification](https://agentskills.io/specification) — the authoritative format definition. Read first when in doubt.
- [`skills-ref`](https://github.com/agentskills/agentskills/tree/main/skills-ref) — the reference validator (`skills-ref validate ./skill-name`).
- [Best practices](https://agentskills.io/skill-creation/best-practices), [Optimizing descriptions](https://agentskills.io/skill-creation/optimizing-descriptions), [Evaluating skills](https://agentskills.io/skill-creation/evaluating-skills) — official companion guides.

**Reference implementations this guide draws from**

- [anthropics/skills](https://github.com/anthropics/skills) — origin of the progressive-disclosure framing, "context is a public good" and "principle of lack of surprise" wording, the docx description example, and the `package_skill.py` / `quick_validate.py` tooling referenced in [`host-claude-code.md`](references/host-claude-code.md).
- [openai/skills](https://github.com/openai/skills) — origin of the six-step creation process, the degrees-of-freedom framing, and the `agents/openai.yaml` adapter pattern detailed in [`host-codex.md`](references/host-codex.md).
