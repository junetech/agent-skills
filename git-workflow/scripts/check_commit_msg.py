"""Check commit message titles against the git-workflow skill's conventions.

Checks each title for exactly three things:
  1. display width <= 49 columns
  2. Conventional Commits prefix: <type>(<scope>)!: <summary>
  3. no trailing period

Imperative mood is not checked -- it cannot be decided mechanically.
The rules themselves live in ../SKILL.md; this script only counts.

Why columns and not bytes or characters: the 50-char convention is about how
wide a title renders in `git log --oneline`. `wc -c` counts bytes, so it triples
a Korean title; a character count undercounts one by half. East Asian Wide and
Fullwidth code points occupy two columns, and are counted so.

Two width approximations, both accepted because `git log --oneline` prefixes an
8-column short SHA, leaving a 49-column title 23 columns of slack at 80:
  - East Asian Ambiguous characters (-> ... ' +- deg) count as 1, per the
    wcwidth convention. Terminals in a CJK locale render them as 2.
  - Emoji width is right for East Asian Wide ones (U+1F680) and for regional
    indicator flags, but text-presentation emoji (U+2764, U+26A0, with or
    without U+FE0F) count 1 where a terminal shows 2, and ZWJ sequences count
    once per component. Fixing those needs the Emoji_Presentation property and
    grapheme cluster segmentation; neither is in the standard library.

Usage:
  python <skill-dir>/scripts/check_commit_msg.py 'TITLE' ['TITLE' ...]

Exit codes:
  0 — every title passes
  1 — one or more violations
  2 — usage error
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata


TITLE_MAX_COLUMNS = 49

# Kept in step with the type list in ../SKILL.md, which is the single source.
TYPES = ("feat", "fix", "refactor", "docs", "perf", "test", "chore")

# <type>(<scope>)!: <summary>. Conventional Commits calls the scope "a noun
# describing a section of the codebase", with no character restriction, so a
# multi-scope such as `fix(skills-ref,spatial-html):` is valid. An earlier
# `[a-z0-9._/-]+` scope class rejected exactly that, on a real commit here.
PREFIX_RE = re.compile(rf"^(?:{'|'.join(TYPES)})(?:\([^()]+\))?!?: \S")

# Nonspacing marks, enclosing marks, and format characters (ZWSP, ZWJ, BOM,
# directional marks) take no columns. `unicodedata.combining()` cannot stand in
# for this test: it returns 0 for Thai vowel signs, for U+FE0F, and for U+200D.
ZERO_WIDTH_CATEGORIES = frozenset({"Mn", "Me", "Cf"})


def display_width(text: str) -> int:
    """Count the terminal columns `text` occupies."""
    width = 0
    for char in text:
        # Zero width is tested first: U+3099 and six others are both a
        # nonspacing mark and East Asian Wide, and the mark wins.
        if unicodedata.category(char) in ZERO_WIDTH_CATEGORIES:
            continue
        width += 2 if unicodedata.east_asian_width(char) in ("W", "F") else 1
    return width


def violations(title: str, width: int) -> list[str]:
    """Return one reason per broken rule, empty when the title is clean."""
    reasons: list[str] = []
    if width > TITLE_MAX_COLUMNS:
        reasons.append(f"title is {width} columns, limit {TITLE_MAX_COLUMNS}")
    if not PREFIX_RE.match(title):
        reasons.append(
            "no Conventional Commits prefix `<type>(<scope>)!: <summary>`; "
            f"type must be one of: {', '.join(TYPES)}"
        )
    if title.endswith("."):
        reasons.append("title ends with a period")
    return reasons


def use_utf8(stream: object) -> None:
    """Stop CPython from encoding output with the locale's codec.

    `sys.stdout.encoding` follows the locale until Python 3.15 -- cp949 on a
    Korean Windows. Echoing a title containing an emoji would raise
    UnicodeEncodeError and exit 1, and a caller reads exit 1 as "the title
    breaks a rule". A checker must not report a violation it never found.
    """
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
    except (AttributeError, ValueError):
        pass  # already replaced (e.g. captured); assume it handles Unicode


def main(argv: list[str] | None = None) -> int:
    use_utf8(sys.stdout)
    use_utf8(sys.stderr)

    parser = argparse.ArgumentParser(
        prog="check_commit_msg.py",
        description="Check commit titles against the git-workflow conventions.",
        epilog="exit: 0 = every title passes, 1 = violation, 2 = usage error",
    )
    # One positional, one mode. There is no second input to silently drop, and
    # no pair of modes to guess between.
    parser.add_argument(
        "titles",
        metavar="TITLE",
        nargs="+",
        help="a commit title to check; repeat for several candidates",
    )
    titles = parser.parse_args(argv).titles

    failed = False
    for title in titles:
        width = display_width(title)
        reasons = violations(title, width)
        # `Title: NN columns ✓` is the output contract in ../SKILL.md, printed
        # here so the agent pastes it rather than recomputing a count it cannot.
        print(f"Title: {width} columns {'✗' if reasons else '✓'}  {title}")
        for reason in reasons:
            print(f"  - {reason}")
        failed = failed or bool(reasons)

    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
