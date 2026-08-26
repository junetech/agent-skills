---
name: pair-programming
description: Implements an already-reviewed coding plan one small semantic step at a time, pausing after each step to show the change and wait for the user's explicit go-ahead before continuing; like a driver checking in with a navigator, not a fresh subagent per task. Use once a plan exists and has already been reviewed (a file in vault/plans/, an approved design doc, or a plan agreed earlier in the conversation) and the user wants to implement it without one large diff to read all at once later ("implement this plan step by step", "let's pair program this", "go one step at a time and wait for me", ...). Each step is checked against a one-screen size budget (2 files, 32-line span, by default); this skill never commits; hand accumulated changes to git-workflow when ready. Not for drafting/reviewing the plan itself, nor a one-shot "just implement all of it" request wanting a single diff.
compatibility: Requires git and one Python 3 implementation on PATH (`python3` on Linux/macOS, `python` on Windows).
---

## Why this exists

A single large diff produced all at once is expensive to read later: the reader has to
hold the whole change in their head to find where their attention is needed. Reviewing
each small piece as it lands is cheaper — the reader's mental model grows one step at a
time instead of being reconstructed after the fact. This skill trades speed for that
cheaper reading: it is slower than implementing everything in one pass, and that is the
point, not a side effect to minimize.

## Step 1: Confirm the plan is settled

Do not draft or re-review the plan here — that already happened. Locate it:

- A plan file the user names or that lives in this repo's `vault/plans/` convention.
- Otherwise, the plan as already agreed upon earlier in the conversation.

If no settled plan exists, say so and stop; do not invent one. If the plan's scope or
order is genuinely ambiguous in a way that changes what "one step" means, ask once before
starting — do not silently guess and do not re-litigate decisions the plan already made.

## Step 2: Decompose into steps, and show the roadmap

Break the plan into steps smaller than a commit-worthy unit — smaller than "one logical
change," down to the size of a single idea a reader can verify in one read: one function
body, one branch of a conditional, one call site wired up, one test case added.

Sizing heuristic: if you can name what a step does without the word "and," it's sized
right. If naming it needs "and," split it further. If a step is so small it isn't really
an idea on its own (e.g. an import line with nothing yet using it), fold it into the step
that gives it meaning instead of presenting it alone.

An intermediate step does not need to build or pass tests on its own — that's a
correctness concern, not a reviewability one. It only needs to be a single coherent idea.

The idea-based heuristic is a judgment call and easy to drift on, so it is backed by a
hard, checked budget: a step's changes must fit on one screen — by default at most 2
files, each with changed lines spanning at most 32 contiguous lines of the new file.
`scripts/check_step_size.py` enforces this from the actual diff (see Step 3); do not
eyeball line counts or file counts yourself, the way `git-workflow` never counts commit
title columns by hand. If the user names a different screen size, pass their numbers to
the script's `--max-files`/`--max-span` flags instead of the defaults.

Track the step list with the task-tracking tool available in the current environment
(e.g. `TodoWrite`) if one is available, so the user sees the full roadmap up front and
its progress as steps complete. Otherwise print the step list once before starting.

## Step 3: Execute one step at a time

Before implementing the first step, run:

```sh
# Linux / macOS
python3 <skill-dir>/scripts/check_step_size.py start
# Windows
python <skill-dir>/scripts/check_step_size.py start
```

`<skill-dir>` is this skill's own directory, which the harness reports when it loads the
skill. Use the interpreter named for the current platform: on Linux `python` is often
absent or aliased to Python 2, while on Windows `python` is the name the installer puts
on PATH. This records a baseline outside the working tree (nothing is staged, stashed, or
committed) so the size check below can later isolate exactly this step's changes, even
though earlier steps' changes are still sitting uncommitted in the working tree.

For each step, in order:

1. Implement exactly that step. Do not get ahead of it — do not also touch code that
   belongs to a later step, even if it would be more efficient to do them together.
2. Run `check_step_size.py check` (same interpreter as above). If it reports `FAIL`,
   the step doesn't fit on one screen: split it and re-implement the smaller pieces, then
   check again. Do not present a step that failed the check. If a step is genuinely one
   idea that cannot be split further (rare — e.g. a mechanical rename touching many call
   sites), tell the user the check failed and why, and ask whether to proceed anyway
   rather than silently overriding it.
3. Show the user what changed: a short description of the idea plus the relevant diff or
   excerpt (not a re-dump of the whole file).
4. Mark the step done in the task tracker if one is in use.
5. Stop. Do not implement the next step until the user responds.

On an approval signal (e.g. "다음", "next", "ok", "go", "lgtm", or similar), run
`check_step_size.py start` again to reset the baseline to the now-approved state, then
move to the next step. On a revision request, revise the current step in place, re-run
`check`, and re-present it — still waiting, not advancing, and not resetting the
baseline yet. If the user explicitly asks to batch several steps or skip the pausing for
a stretch, follow that instruction for as long as they've asked; it overrides the default
pacing without ending the skill.

If, mid-implementation, a step turns out to conflict with the plan or reveals the plan
was wrong about something, stop and report the discrepancy — do not silently deviate from
the reviewed plan to make the code work.

## Step 4: Finish without committing

Never create a git commit as part of this skill, per-step or at the end — steps are
deliberately finer-grained than a commit, and grouping them into commits is a separate
decision the user makes afterward. When the last step is approved, summarize what was
implemented across all steps and any deviations from the plan, then stop. If the user
wants to commit the accumulated work, hand off to the git-workflow skill rather than
drafting a commit message here.
