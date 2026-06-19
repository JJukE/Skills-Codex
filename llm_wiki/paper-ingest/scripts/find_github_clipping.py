#!/usr/bin/env python3
"""Find raw GitHub clipping candidates for a paper without modifying files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def read_prefix(path: Path, max_chars: int = 12000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:max_chars]
    except OSError:
        return ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True, help="Paper title or method name.")
    parser.add_argument("--authors", default="", help="Comma-separated author names.")
    parser.add_argument("--raw-github", default="raw/github", help="Raw GitHub clipping directory.")
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(args.raw_github)
    if not root.exists():
        raise SystemExit(f"GitHub clipping directory does not exist: {root}")

    stop = {"the", "and", "for", "with", "via", "towards", "toward", "from", "using", "into"}
    title_terms = [t for t in normalize(args.title).split() if t not in stop]
    author_terms = [t for t in normalize(args.authors).split() if len(t) > 2]

    results: list[dict[str, object]] = []
    for path in sorted(root.glob("*.md")):
        text = normalize(path.name + "\n" + read_prefix(path))
        score = 0
        for term in title_terms:
            if term in text:
                score += 4 if len(term) > 4 else 1
        for term in author_terms:
            if term in text:
                score += 2
        if "github com" in text:
            score += 2
        if score > 0:
            results.append({"score": score, "path": str(path), "name": path.name})

    results.sort(key=lambda item: (-int(item["score"]), str(item["path"])))
    results = results[: args.limit]

    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        for item in results:
            print(f'{item["score"]:>3}  {item["path"]}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

