# Pre-Landing Review Checklist

## Instructions

Review the `git diff origin/<base>` output for the issues listed below. Be specific — cite `file:line` and suggest fixes. Skip anything that's fine. Only flag real problems.

Language-specific patterns are tagged `[js]`, `[ts]`, `[py]`, `[go]`, `[rs]`, `[rb]`, `[ex]`, `[java]`. Apply only the patterns relevant to the detected language(s). Untagged patterns apply to all languages.

**Two-pass review:**

- **Pass 1 (CRITICAL):** SQL & Data Safety, Race Conditions & Concurrency, LLM Output Trust Boundary, Enum & Value Completeness
- **Pass 2 (INFORMATIONAL):** All remaining categories

All findings get action via Fix-First Review: obvious mechanical fixes are applied automatically, genuinely ambiguous issues are batched into a single user question.

**Output format:**

```txt
Pre-Landing Review: N issues (X critical, Y informational)

**AUTO-FIXED:**
- [file:line] Problem → fix applied

**NEEDS INPUT:**
- [file:line] Problem description
  Recommended fix: suggested fix
```

If no issues found: `Pre-Landing Review: No issues found.`

Be terse. For each issue: one line describing the problem, one line with the fix. No preamble, no summaries, no "looks good overall."

---

## Review Categories

### Pass 1 — CRITICAL

#### SQL & Data Safety

String interpolation or concatenation used to build SQL queries instead of parameterized queries / prepared statements:

- `[py]` f-strings or `%` formatting inside `cursor.execute()`, `.raw()`, `.extra()`
- `[js][ts]` template literals in `query()`, `.raw()`, Knex `.whereRaw()` / `.joinRaw()`
- `[go]` `fmt.Sprintf` used to build query strings passed to `db.Query` / `db.Exec`
- `[rs]` string format macros used to construct SQL passed to `sqlx` / `diesel`
- `[rb]` string interpolation in `.where()`, `.find_by_sql()`, `execute()`; values converted with `.to_i` or `.to_f` are still flagged — use parameterized form

TOCTOU: check-then-set patterns that should be atomic (read-then-write without a conditional `WHERE` in the update).

`UPDATE` without a `WHERE` clause constraining the old state — concurrent updates can double-apply transitions.

ORM escape hatches that bypass validation or constraints:

- `[rb]` `update_column` / `update_columns`
- `[py]` `.update()` with `save=False` on fields that have constraints
- `[js][ts]` Prisma `updateMany` without a unique filter when targeting a single record

N+1 queries: associations or related records fetched inside a loop without batch loading:

- `[rb]` missing `.includes()` / `.preload()`
- `[py]` missing `select_related()` / `prefetch_related()`
- `[js][ts]` missing DataLoader or batch fetch for repeated per-item DB calls

#### Race Conditions & Concurrency

Read-check-write without a uniqueness constraint or duplicate-handling:

- `[rb]` `where(...).first || create(...)` without a unique DB index + `rescue RecordNotUnique`
- `[py]` `get_or_create()` / `filter().first()` then `save()` without `unique_together` and `IntegrityError` handling
- `[go]` select-then-insert without `ON CONFLICT` or error handling on duplicate key
- `[js][ts]` `findOne` then `create` / `insert` without unique index + conflict handling

`find_or_create` / `get_or_create` equivalents on columns without a unique DB index — concurrent calls can produce duplicates.

Status/state transitions that don't atomically assert the old state in the `WHERE` clause — concurrent requests can skip or double-apply the transition.

XSS: user-controlled data rendered without escaping:

- `[rb]` `.html_safe`, `raw()`, or string interpolation into `html_safe` output
- `[js][ts]` `dangerouslySetInnerHTML`, `innerHTML =`, `document.write()` with unsanitized input
- `[py]` `mark_safe()` in Django templates; Jinja2 `| safe` filter on user input
- `[go]` `template/text` used instead of `template/html`; `template.HTML()` cast on user input

#### LLM Output Trust Boundary

LLM-generated values (emails, URLs, names, IDs) written to the database or passed to external services without format validation. Add lightweight guards (regex, URL parse, `.strip()`) before persisting.

Structured LLM output (arrays, objects/dicts) accepted without type or shape checks before database writes. Validate that expected keys exist and values are the expected type.

#### Enum & Value Completeness

When the diff introduces a new enum value, status string, tier name, or type constant:

- **Trace it through every consumer.** Read (don't just grep — READ) each file that switches on, filters by, or displays that value. If any consumer doesn't handle the new value, flag it.
- **Check allowlists/filter arrays.** Search for arrays or lists containing sibling values and verify the new value is included where needed.
- **Check `switch`/`match`/`case`/`if-elsif` chains.** If existing code branches on the enum, does the new value fall through to a wrong default?

Use Grep to find all references to sibling values. Read each match. This step requires reading code OUTSIDE the diff.

---

### Pass 2 — INFORMATIONAL

#### Conditional Side Effects

Code paths that branch on a condition but forget to apply a required side effect on one branch. Example: a record promoted to a new status but an associated field only set when a secondary condition is true — the other branch promotes without the field, creating an inconsistent record.

Log messages that claim an action happened when the action was conditionally skipped. The log should reflect what actually occurred.

#### Magic Numbers & String Coupling

Bare numeric literals used across multiple files — should be named constants.

Error message strings used as filter values elsewhere — grep for the string to check if anything matches on it. These should be constants, not duplicated literals.

#### Dead Code & Consistency

Variables assigned but never read.

Version mismatch: PR title or commit message references a version that doesn't match `VERSION`, `CHANGELOG`, `package.json`, `Cargo.toml`, `pyproject.toml`, or equivalent.

CHANGELOG entries that describe changes inaccurately (e.g., "changed from X to Y" when X never existed).

Comments or docstrings that describe old behavior after the code changed.

#### LLM Prompt Issues

0-indexed lists in prompts — LLMs reliably return 1-indexed output for numbered lists.

Prompt text listing available tools or capabilities that don't match what's actually wired up in the tools array / tool registry.

Word or token limits stated in multiple places that could drift out of sync.

#### Test Gaps

Negative-path tests that assert type or status but not the side effects (field populated? callback fired? external call made?).

Assertions on string content without checking format (e.g., asserting a URL is present but not that it's a valid URL).

Missing assertion that an external service was NOT called on a code path that should skip it.

Security-enforcement features (auth checks, rate limiting, blocking) without a test verifying the enforcement path works end-to-end.

#### Completeness Gaps

Partial enum handling where adding the remaining cases is straightforward.

Incomplete error paths where the happy path is handled but error/nil/null cases silently fall through.

Missing edge cases (empty input, zero, boundary values) where adding them mirrors the structure of existing tests.

Features implemented at 80-90% where the remaining 10% is a clear, bounded addition.

#### Crypto & Entropy

Truncation instead of hashing (last N chars of a string used as an ID) — lower entropy, easier collisions. Use SHA-256 or equivalent.

Weak or non-cryptographic random for security-sensitive values:

- `[py]` `random.random()` / `random.choice()` instead of `secrets`
- `[js][ts]` `Math.random()` instead of `crypto.getRandomValues()` / `crypto.randomBytes()`
- `[go]` `math/rand` instead of `crypto/rand`
- `[rb]` `rand()` / `Random.rand` instead of `SecureRandom`
- `[rs]` `rand` crate instead of `ring` / `getrandom` for security-sensitive values

Non-constant-time comparison (`==`) on secrets, tokens, or HMACs — vulnerable to timing attacks. Use a constant-time compare function.

#### Time Window Safety

Date-key lookups that assume "today" covers a full 24 hours — a process starting at 08:00 only sees midnight→08:00 under today's key.

Mismatched time windows between related features — one uses hourly buckets, another uses daily keys for the same underlying data.

#### Type Coercion at Boundaries

Values crossing language→JSON→language boundaries where the type could change (numeric vs. string). Hash or digest inputs must normalize types before serialization — `{ cores: 8 }` and `{ cores: "8" }` produce different hashes.

Integer/string ambiguity in API request/response schemas not caught by the type system.

#### View / Frontend

Inline `<style>` blocks in partials or components that are re-parsed on every render — move to a stylesheet.

O(n²) lookups in rendering: `Array.find` / `.find {}` / `list.index()` inside a loop over the same collection — use a pre-built map/dict/hash.

Application-level filtering on DB results that could be a `WHERE` clause (unless intentionally post-filtering for a reason noted in the code).

---

## Severity Classification

```txt
CRITICAL (highest severity):        INFORMATIONAL (lower severity):
├─ SQL & Data Safety                ├─ Conditional Side Effects
├─ Race Conditions & Concurrency    ├─ Magic Numbers & String Coupling
├─ LLM Output Trust Boundary        ├─ Dead Code & Consistency
└─ Enum & Value Completeness        ├─ LLM Prompt Issues
                                    ├─ Test Gaps
                                    ├─ Completeness Gaps
                                    ├─ Crypto & Entropy
                                    ├─ Time Window Safety
                                    ├─ Type Coercion at Boundaries
                                    └─ View / Frontend

All findings are actioned via Fix-First Review. Severity determines
presentation order and classification of AUTO-FIX vs ASK — critical
findings lean toward ASK (they're riskier), informational findings
lean toward AUTO-FIX (they're more mechanical).
```

---

## Fix-First Heuristic

Determines whether the agent auto-fixes a finding or asks the user.

```txt
AUTO-FIX (agent fixes without asking):     ASK (needs human judgment):
├─ Dead code / unused variables            ├─ Security (auth, XSS, injection)
├─ N+1 queries (missing batch load)        ├─ Race conditions
├─ Stale comments contradicting code       ├─ Design decisions
├─ Magic numbers → named constants         ├─ Large fixes (>20 lines)
├─ Missing LLM output format validation    ├─ Enum completeness
├─ Version / path mismatches               ├─ Removing functionality
├─ Variables assigned but never read       └─ Anything changing user-visible
└─ Inline styles, O(n²) view lookups          behavior
```

**Rule of thumb:** If the fix is mechanical and a senior engineer would apply it without discussion, it's AUTO-FIX. If reasonable engineers could disagree, it's ASK.

**Critical findings default toward ASK** — they're inherently riskier.
**Informational findings default toward AUTO-FIX** — they're more mechanical.

---

## Suppressions — DO NOT flag these

- Redundancy that is harmless and aids readability
- "Add a comment explaining why this threshold was chosen" — thresholds change during tuning, comments rot
- "This assertion could be tighter" when the assertion already covers the behavior
- Consistency-only changes (wrapping a value to match how another constant is guarded)
- "Regex doesn't handle edge case X" when the input is constrained and X never occurs in practice
- "Test exercises multiple guards simultaneously" — tests don't need to isolate every guard
- Eval threshold changes — these are tuned empirically and change constantly
- Harmless no-ops
- ANYTHING already addressed in the diff you're reviewing — read the FULL diff before commenting
