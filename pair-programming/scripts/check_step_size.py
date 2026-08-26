#!/usr/bin/env python3
"""Enforce a one-screen size budget on the uncommitted changes made since the
last recorded baseline: at most --max-files distinct files, each with changed
lines spanning at most --max-span contiguous lines in the new file content.

Usage:
  check_step_size.py start
      Record the current working-tree state as the baseline for the next step.
      Run this once before starting a step (and again after each step is
      approved, to reset the baseline for the following step).

  check_step_size.py check [--max-files N] [--max-span N]
      Diff the working tree against the last recorded baseline and report
      PASS/FAIL. Run this after implementing a step, before presenting it.

The baseline is stored at <git-dir>/PAIR_PROGRAMMING_BASELINE, outside the
working tree, so it never shows up as a tracked or untracked file.
"""
import argparse
import re
import subprocess
import sys


def run(args, check=True):
    result = subprocess.run(
        args, capture_output=True, text=True,
    )
    if check and result.returncode != 0:
        sys.stderr.write(f"$ {' '.join(args)}\n{result.stderr}")
        sys.exit(1)
    return result.stdout


def git_dir():
    return run(["git", "rev-parse", "--git-dir"]).strip()


def baseline_path():
    return f"{git_dir()}/PAIR_PROGRAMMING_BASELINE"


def untracked_files():
    out = run(["git", "status", "--porcelain=v1", "--untracked-files=all"])
    files = []
    for line in out.splitlines():
        if line.startswith("?? "):
            files.append(line[3:].strip())
    return set(files)


def cmd_start(_args):
    stash_hash = run(["git", "stash", "create"]).strip()
    if not stash_hash:
        stash_hash = run(["git", "rev-parse", "HEAD"]).strip()
    untracked = sorted(untracked_files())
    with open(baseline_path(), "w") as f:
        f.write(stash_hash + "\n")
        for path in untracked:
            f.write(path + "\n")
    print(f"Baseline recorded: {stash_hash} ({len(untracked)} pre-existing untracked files)")


HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def parse_tracked_spans(baseline_hash):
    """Return {path: (min_line, max_line) | "deleted"} for files changed since baseline."""
    diff = run(["git", "diff", "--unified=0", baseline_hash, "--"], check=False)
    spans = {}
    path = None
    is_deletion = False
    for line in diff.splitlines():
        if line.startswith("diff --git "):
            path = None
            is_deletion = False
        elif line.startswith("--- "):
            old_path = line[4:].strip()
            if old_path != "/dev/null":
                path = old_path[2:] if old_path.startswith("a/") else old_path
        elif line.startswith("+++ "):
            new_path = line[4:].strip()
            if new_path == "/dev/null":
                is_deletion = True
                # path already set from the "--- a/..." line above.
            else:
                path = new_path[2:] if new_path.startswith("b/") else new_path
            if path is not None:
                spans[path] = "deleted" if is_deletion else None
        elif line.startswith("@@ ") and path is not None and not is_deletion:
            m = HUNK_RE.match(line)
            if not m:
                continue
            start = int(m.group(1))
            length = int(m.group(2)) if m.group(2) is not None else 1
            end = start + max(length, 1) - 1
            prev = spans.get(path)
            if prev in (None, "deleted"):
                spans[path] = (start, end)
            else:
                spans[path] = (min(prev[0], start), max(prev[1], end))
    return spans


def cmd_check(args):
    try:
        with open(baseline_path()) as f:
            lines = f.read().splitlines()
    except FileNotFoundError:
        print("No baseline found. Run 'check_step_size.py start' before implementing a step.")
        sys.exit(2)

    baseline_hash, baseline_untracked = lines[0], set(lines[1:])

    spans = parse_tracked_spans(baseline_hash)
    new_untracked = sorted(untracked_files() - baseline_untracked)

    rows = []  # (path, span_text, ok)
    for path, span in spans.items():
        if span == "deleted":
            rows.append((path, "deleted", True))
        elif span is None:
            continue
        else:
            start, end = span
            length = end - start + 1
            ok = length <= args.max_span
            rows.append((path, f"lines {start}-{end} (span {length})", ok))

    for path in new_untracked:
        try:
            with open(path) as f:
                length = sum(1 for _ in f)
        except (OSError, UnicodeDecodeError):
            length = None
        if length is None:
            rows.append((path, "new file (binary or unreadable)", True))
        else:
            ok = length <= args.max_span
            rows.append((path, f"new file, {length} lines", ok))

    files_ok = len(rows) <= args.max_files
    all_ok = files_ok and all(ok for _, _, ok in rows)

    print(f"Step size check (limits: max {args.max_files} files, max {args.max_span}-line span):")
    print(f"Files touched: {len(rows)} {'OK' if files_ok else 'FAIL'}")
    for path, detail, ok in rows:
        print(f"  - {path}: {detail} [{'OK' if ok else 'FAIL'}]")
    print(f"Result: {'PASS' if all_ok else 'FAIL'}")
    sys.exit(0 if all_ok else 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("start")

    check_parser = sub.add_parser("check")
    check_parser.add_argument("--max-files", type=int, default=2)
    check_parser.add_argument("--max-span", type=int, default=32)

    args = parser.parse_args()
    if args.command == "start":
        cmd_start(args)
    elif args.command == "check":
        cmd_check(args)


if __name__ == "__main__":
    main()
