"""Validate md-to-spatial-html generated HTML.

This script checks deterministic failure modes for the skill. It does not
convert markdown and does not judge visual quality.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
from pathlib import Path


HEADING_RE = re.compile(r"^(#{2,6})\s+(.+?)\s*#*\s*$", re.MULTILINE)
FENCE_RE = re.compile(r"^\s*```", re.MULTILINE)


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


def check(args: argparse.Namespace) -> list[str]:
    errors: list[str] = []
    source = Path(args.source)
    html_path = Path(args.html)

    if not source.exists():
        errors.append(f"source file does not exist: {source}")
        return errors
    if not html_path.exists():
        errors.append(f"html file does not exist: {html_path}")
        return errors

    markdown = source.read_text(encoding="utf-8")
    html_text = html_path.read_text(encoding="utf-8")
    html_lower = html_text.lower()

    if "{{" in html_text:
        errors.append("unreplaced {{...}} placeholder remains")

    if re.search(r"<\s*script\b", html_text, flags=re.IGNORECASE):
        errors.append("script tag is not allowed")
    if re.search(r"<\s*link\b", html_text, flags=re.IGNORECASE):
        errors.append("link tag is not allowed")
    if re.search(r"\b(?:src|href)\s*=\s*[\"']https?://", html_text, flags=re.IGNORECASE):
        errors.append("remote src/href asset is not allowed")
    if re.search(r"url\(\s*[\"']?https?://", html_text, flags=re.IGNORECASE):
        errors.append("remote CSS url(...) asset is not allowed")

    if "source:" not in html_lower:
        errors.append("footer attribution is missing 'Source:'")
    elif not any(candidate in html_text for candidate in normalize_path_text(source)):
        errors.append(f"footer attribution does not reference source path or filename: {source}")

    expected_code_blocks = count_markdown_code_blocks(markdown)
    if expected_code_blocks:
        pre_count = len(re.findall(r"<\s*pre\b", html_text, flags=re.IGNORECASE))
        code_count = len(re.findall(r"<\s*code\b", html_text, flags=re.IGNORECASE))
        if pre_count < expected_code_blocks or code_count < expected_code_blocks:
            errors.append(
                "code block count mismatch: "
                f"markdown has {expected_code_blocks}, html has {pre_count} <pre> and {code_count} <code>"
            )

    missing_anchors = []
    for heading_text, slug in find_h2_plus_headings(markdown):
        id_pattern = rf"\bid\s*=\s*[\"']{re.escape(slug)}[\"']"
        href_pattern = rf"\bhref\s*=\s*[\"']#{re.escape(slug)}[\"']"
        if not re.search(id_pattern, html_text, flags=re.IGNORECASE) and not re.search(
            href_pattern, html_text, flags=re.IGNORECASE
        ):
            missing_anchors.append(heading_text)
    if missing_anchors:
        errors.append("missing anchors for headings: " + ", ".join(missing_anchors))

    for peer in args.peer:
        peer_path = Path(peer)
        if not peer_path.exists():
            errors.append(f"peer file does not exist: {peer_path}")
            continue
        if peer_path.name not in html_text:
            errors.append(f"peer link is missing peer filename: {peer_path.name}")

    if args.require_modmap and not has_modmap_svg(html_text):
        errors.append("required figure.modmap containing svg is missing")
    if args.forbid_svg and re.search(r"<\s*svg\b", html_text, flags=re.IGNORECASE):
        errors.append("svg is forbidden for this source but was found")

    return errors


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate md-to-spatial-html output.")
    parser.add_argument("--source", required=True, help="Source markdown file.")
    parser.add_argument("--html", required=True, help="Generated HTML file.")
    parser.add_argument("--peer", action="append", default=[], help="Expected linked peer HTML file.")
    parser.add_argument("--require-modmap", action="store_true", help="Require figure.modmap containing SVG.")
    parser.add_argument("--forbid-svg", action="store_true", help="Fail if any inline SVG is present.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    errors = check(args)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
