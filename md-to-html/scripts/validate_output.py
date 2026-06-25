"""Validate md-to-html generated HTML.

Mode-aware rewrite of the original md-to-spatial-html validator.
Checks deterministic failure modes per the md-to-html skill spec.
Does not convert markdown and does not judge visual quality.

Usage:
  python md-to-html/scripts/validate_output.py \\
    --mode {document,editor,deck,sandbox} \\
    --source <source.md> --html <output.html> \\
    [--peer <peer.html>] \\
    [--require-modmap] \\
    [--forbid-svg] \\
    [--require-export]

Exit codes:
  0 — OK (or warnings only)
  1 — one or more errors
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Regex helpers
# ---------------------------------------------------------------------------

HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*#*\s*$", re.MULTILINE)
FENCE_RE = re.compile(r"^\s*```", re.MULTILINE)

# Network call patterns — banned in ALL modes (invariant 9)
NETWORK_PATTERNS: list[tuple[str, str]] = [
    (r"\bfetch\s*\(", "fetch("),
    (r"\bXMLHttpRequest\b", "XMLHttpRequest"),
    (r"\bWebSocket\s*\(", "WebSocket("),
    (r"\bEventSource\s*\(", "EventSource("),
    (r"\bnavigator\.sendBeacon\b", "navigator.sendBeacon"),
    # URL import() — matches import("http or import('http
    (r"\bimport\s*\(\s*[\"']https?://", "URL import(http...)"),
]

# External asset patterns — banned in ALL modes
EXTERNAL_ASSET_PATTERNS: list[tuple[str, str]] = [
    (r"<\s*link\b", "<link>"),
    (r"\b(?:src|href)\s*=\s*[\"']https?://", "remote src/href"),
    (r"url\(\s*[\"']?https?://", "remote CSS url(...)"),
    (r"@import\s+url\s*\(\s*[\"']?https?://", "@import url(http...)"),
]

# Export affordance patterns for --require-export
EXPORT_BTN_RE = re.compile(
    r"copy|export|download",
    re.IGNORECASE,
)
MDH_EXPORT_RE = re.compile(
    r"MDH\.(copy|download)",
    re.IGNORECASE,
)

# Progressive enhancement patterns (soft check)
PE_DECK_RE = re.compile(r"mdh-slide\b", re.IGNORECASE)
PE_EDITOR_ROW_RE = re.compile(r"mdh-card|mdh-flag|mdh-var-row|mdh-param\b", re.IGNORECASE)


# ---------------------------------------------------------------------------
# Utility functions
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"[*_\[\]()]|#+", "", text)
    text = text.strip().lower()
    text = re.sub(r"[^\w]+", "-", text, flags=re.UNICODE)
    return text.strip("-")


def normalize_path_text(path: Path) -> set[str]:
    raw = str(path)
    slash = raw.replace("\\", "/")
    return {
        raw,
        slash,
        path.name,
        html.escape(raw),
        html.escape(slash),
        html.escape(path.name),
    }


def count_markdown_code_blocks(markdown: str) -> int:
    fence_count = len(FENCE_RE.findall(markdown))
    return fence_count // 2


def find_h2_plus_headings(markdown: str) -> list[tuple[str, str]]:
    headings: list[tuple[str, str]] = []
    for match in HEADING_RE.finditer(markdown):
        text = match.group(2).strip()
        slug = slugify(text)
        if slug:
            headings.append((text, slug))
    return headings


def has_modmap_svg(html_text: str) -> bool:
    return bool(
        re.search(
            r"<figure\b[^>]*class=[\"'][^\"']*\bmodmap\b[^\"']*[\"'][^>]*>.*?<svg\b",
            html_text,
            flags=re.IGNORECASE | re.DOTALL,
        )
    )


# ---------------------------------------------------------------------------
# Check functions
# ---------------------------------------------------------------------------

def check_universal(
    html_text: str,
    source: Path,
    args: argparse.Namespace,
) -> tuple[list[str], list[str]]:
    """Checks that apply to ALL modes. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    # 1. No unreplaced placeholders
    if re.search(r"\{\{\s*[A-Z_]+\s*\}\}", html_text):
        errors.append("unreplaced {{...}} placeholder remains")

    # 2. External asset ban (link, remote src/href, remote CSS url)
    for pattern, label in EXTERNAL_ASSET_PATTERNS:
        if re.search(pattern, html_text, flags=re.IGNORECASE):
            errors.append(f"external/remote asset not allowed: {label}")

    # 3. External JS via <script src=...>
    if re.search(r"<\s*script\b[^>]*\bsrc\s*=", html_text, flags=re.IGNORECASE):
        errors.append("<script src=...> (external JS) is not allowed in any mode")

    # 4. Network call ban (invariant 9) — check inside <script> blocks
    script_blocks = re.findall(
        r"<\s*script\b[^>]*>(.*?)</\s*script\s*>",
        html_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    script_text = "\n".join(script_blocks)
    for pattern, label in NETWORK_PATTERNS:
        if re.search(pattern, script_text, flags=re.IGNORECASE):
            errors.append(f"network call not allowed (invariant 9): {label}")

    # 5. Footer attribution
    html_lower = html_text.lower()
    if "source:" not in html_lower:
        errors.append("footer attribution is missing 'Source:'")
    elif not any(candidate in html_text for candidate in normalize_path_text(source)):
        errors.append(
            f"footer attribution does not reference source path or filename: {source}"
        )

    # 6. Peer link check (optional, applies to all modes)
    for peer in args.peer:
        peer_path = Path(peer)
        if not peer_path.exists():
            errors.append(f"peer file does not exist: {peer_path}")
        elif peer_path.name not in html_text:
            errors.append(f"peer link is missing peer filename: {peer_path.name}")

    return errors, warnings


def check_document_mode(
    html_text: str,
    markdown: str,
    source: Path,
    args: argparse.Namespace,
) -> tuple[list[str], list[str]]:
    """Document-mode-specific checks. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    # Inline <script> is forbidden in document mode
    if re.search(r"<\s*script\b", html_text, flags=re.IGNORECASE):
        errors.append("inline <script> is not allowed in document mode (use --mode editor/deck/sandbox for JS)")

    # Code block count check
    expected_code_blocks = count_markdown_code_blocks(markdown)
    if expected_code_blocks:
        pre_count = len(re.findall(r"<\s*pre\b", html_text, flags=re.IGNORECASE))
        code_count = len(re.findall(r"<\s*code\b", html_text, flags=re.IGNORECASE))
        if pre_count < expected_code_blocks or code_count < expected_code_blocks:
            errors.append(
                f"code block count mismatch: "
                f"markdown has {expected_code_blocks}, "
                f"html has {pre_count} <pre> and {code_count} <code>"
            )

    # Heading anchor check
    missing_anchors: list[str] = []
    for heading_text, slug in find_h2_plus_headings(markdown):
        id_pattern = rf"\bid\s*=\s*[\"']{re.escape(slug)}[\"']"
        href_pattern = rf"\bhref\s*=\s*[\"']#{re.escape(slug)}[\"']"
        if not re.search(id_pattern, html_text, flags=re.IGNORECASE) and not re.search(
            href_pattern, html_text, flags=re.IGNORECASE
        ):
            missing_anchors.append(heading_text)
    if missing_anchors:
        errors.append("missing anchors for headings: " + ", ".join(missing_anchors))

    # require-modmap (document only)
    if args.require_modmap and not has_modmap_svg(html_text):
        errors.append("required figure.modmap containing svg is missing")

    # forbid-svg (document only)
    if args.forbid_svg and re.search(r"<\s*svg\b", html_text, flags=re.IGNORECASE):
        errors.append("svg is forbidden for this source but was found")

    return errors, warnings


def check_interactive_mode(
    html_text: str,
    mode: str,
    args: argparse.Namespace,
) -> tuple[list[str], list[str]]:
    """Editor/deck/sandbox checks. Returns (errors, warnings)."""
    errors: list[str] = []
    warnings: list[str] = []

    # require-export check (mandatory for editor/sandbox, optional for deck)
    if args.require_export or mode in ("editor", "sandbox"):
        # Must have a copy/export/download button-like element
        has_btn = bool(re.search(
            r"<\s*button[^>]*>.*?(?:copy|export|download).*?</\s*button\s*>",
            html_text,
            flags=re.IGNORECASE | re.DOTALL,
        ))
        has_mdh = bool(MDH_EXPORT_RE.search(html_text))
        if not has_btn:
            errors.append(
                f"export affordance missing: no <button> with copy/export/download text "
                f"(mode={mode}, --require-export)"
            )
        if not has_mdh:
            errors.append(
                f"export affordance missing: MDH.copy or MDH.download not found in script "
                f"(mode={mode}, --require-export)"
            )

    # Progressive enhancement soft warnings
    if mode == "deck":
        if not PE_DECK_RE.search(html_text):
            warnings.append(
                "WARN: deck mode but no .mdh-slide elements found in DOM — "
                "JS-off fallback may be empty (invariant 8)"
            )
    elif mode == "editor":
        if not PE_EDITOR_ROW_RE.search(html_text):
            warnings.append(
                "WARN: editor mode but no data-row elements (.mdh-card/.mdh-flag/.mdh-param) "
                "found in static DOM — JS-off fallback may be empty (invariant 8)"
            )

    return errors, warnings


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def check(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    """Run all checks. Returns (errors, warnings)."""
    all_errors: list[str] = []
    all_warnings: list[str] = []

    source = Path(args.source)
    html_path = Path(args.html)

    if not source.exists():
        all_errors.append(f"source file does not exist: {source}")
        return all_errors, all_warnings
    if not html_path.exists():
        all_errors.append(f"html file does not exist: {html_path}")
        return all_errors, all_warnings

    markdown = source.read_text(encoding="utf-8")
    html_text = html_path.read_text(encoding="utf-8")

    # Universal checks (all modes)
    errs, warns = check_universal(html_text, source, args)
    all_errors.extend(errs)
    all_warnings.extend(warns)

    # Mode-specific checks
    mode = args.mode
    if mode == "document":
        errs, warns = check_document_mode(html_text, markdown, source, args)
        all_errors.extend(errs)
        all_warnings.extend(warns)
    else:
        errs, warns = check_interactive_mode(html_text, mode, args)
        all_errors.extend(errs)
        all_warnings.extend(warns)

    return all_errors, all_warnings


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Validate md-to-html output. "
            "Exit 1 if errors; exit 0 for warnings-only or clean."
        )
    )
    parser.add_argument(
        "--mode",
        choices=["document", "editor", "deck", "sandbox"],
        default="document",
        help="Output mode (default: document).",
    )
    parser.add_argument("--source", required=True, help="Source markdown file.")
    parser.add_argument("--html", required=True, help="Generated HTML file.")
    parser.add_argument(
        "--peer",
        action="append",
        default=[],
        help="Expected linked peer HTML file (repeatable).",
    )
    parser.add_argument(
        "--require-modmap",
        action="store_true",
        help="(document mode) Require figure.modmap containing SVG.",
    )
    parser.add_argument(
        "--forbid-svg",
        action="store_true",
        help="(document mode) Fail if any inline SVG is present.",
    )
    parser.add_argument(
        "--require-export",
        action="store_true",
        help="Require copy/export/download control + MDH.copy or MDH.download. "
             "Implicitly set for editor and sandbox modes.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    errors, warnings = check(args)

    for warn in warnings:
        print(warn, file=sys.stderr)

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    if warnings:
        print("OK (with warnings)")
    else:
        print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
