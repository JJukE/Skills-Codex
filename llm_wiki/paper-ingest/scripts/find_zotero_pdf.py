#!/usr/bin/env python3
"""Find Zotero-managed PDF candidates without modifying any files."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ZOTERO_PDF_ROOT_PATH = Path(
    "~/Library/Mobile Documents/iCloud~QReader~MarginStudy~easy/Documents/Zotero"
).expanduser()


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def score(path: Path, query_terms: list[str], year: str | None) -> int:
    haystack = normalize(str(path))
    total = 0
    for term in query_terms:
        if term and term in haystack:
            total += 3 if len(term) > 4 else 1
    if year and year in path.name:
        total += 8
    return total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True, help="Paper title or distinctive title fragment.")
    parser.add_argument("--year", help="Publication year, if known.")
    parser.add_argument(
        "--root",
        default=str(ZOTERO_PDF_ROOT_PATH),
        help="Zotero PDF root. Defaults to the machine-specific zotero_pdf_root_path configured in this skill.",
    )
    parser.add_argument("--limit", type=int, default=10, help="Maximum candidates to print.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of plain text.")
    args = parser.parse_args()

    root = Path(args.root).expanduser()
    if not root.exists():
        raise SystemExit(f"Zotero root does not exist: {root}")

    stop = {"the", "and", "for", "with", "via", "towards", "toward", "from", "using", "into"}
    query_terms = [t for t in normalize(args.title).split() if t not in stop]

    candidates: list[dict[str, object]] = []
    for path in root.rglob("*.pdf"):
        value = score(path, query_terms, args.year)
        if value > 0:
            candidates.append(
                {
                    "score": value,
                    "path": str(path),
                    "name": path.name,
                    "size_bytes": path.stat().st_size,
                }
            )

    candidates.sort(key=lambda item: (-int(item["score"]), str(item["path"])))
    candidates = candidates[: args.limit]

    if args.json:
        print(json.dumps(candidates, ensure_ascii=False, indent=2))
    else:
        for item in candidates:
            print(f'{item["score"]:>3}  {item["path"]}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
