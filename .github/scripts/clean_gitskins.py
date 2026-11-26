"""Fetch live GitSkins SVG cards and strip branding watermarks."""

from __future__ import annotations

import os
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "posathanmai1-lang")
OUT_DIR = Path(sys.argv[1] if len(sys.argv) > 1 else "dist")

SECTIONS = {
    "stats": f"https://www.gitskins.com/api/section/stats?username={USERNAME}&theme=github-dark&mode=dark",
    "stack": f"https://www.gitskins.com/api/section/stack?username={USERNAME}&theme=github-dark&mode=dark",
    "heatmap": f"https://www.gitskins.com/api/section/heatmap?username={USERNAME}&theme=github-dark&mode=dark",
}

ARIA_LABELS = {
    "stats": "GitHub Profile Signal",
    "stack": "GitHub Language Stack",
    "heatmap": "GitHub Contribution Activity",
}

WATERMARK_TEXT_RE = re.compile(
    r"\s*<text\b[^>]*>[^<]*gitskins\.com[^<]*</text>",
    re.IGNORECASE,
)
ARIA_RE = re.compile(r'aria-label="GitSkins[^"]*"', re.IGNORECASE)


def clean_svg(raw: str, section: str) -> str:
    """Remove gitskins.com watermarks and promotional subtitles from an SVG."""
    cleaned = WATERMARK_TEXT_RE.sub("", raw)
    cleaned = cleaned.replace(
        "Live GitHub stats styled by GitSkins",
        "Live GitHub repository &amp; contribution telemetry",
    )
    cleaned = re.sub(
        r"\s*styled by\s+gitskins",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )
    cleaned = ARIA_RE.sub(f'aria-label="{ARIA_LABELS[section]}"', cleaned)

    # Verify XML parses cleanly before writing.
    ET.fromstring(cleaned.encode("utf-8"))
    return cleaned


def fetch_svg(url: str) -> str:
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; GitHubProfileSync/1.0)"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"Unexpected status {resp.status} for {url}")
        return resp.read().decode("utf-8")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name, url in SECTIONS.items():
        raw = fetch_svg(url)
        cleaned = clean_svg(raw, name)
        target = OUT_DIR / f"{name}.svg"
        target.write_text(cleaned, encoding="utf-8")
        print(f"Wrote clean {target} ({len(cleaned)} bytes)")


if __name__ == "__main__":
    main()
