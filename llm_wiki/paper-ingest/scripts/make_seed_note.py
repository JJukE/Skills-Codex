#!/usr/bin/env python3
"""Generate a raw Zotero seed note skeleton for review or writing."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path


def sanitize_filename(text: str) -> str:
    text = re.sub(r"[\\/:*?\"<>|]+", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def note_text(args: argparse.Namespace) -> str:
    authors = [a.strip() for a in args.authors.split(",") if a.strip()]
    author_yaml = "\n".join(f"  - {author}" for author in authors) or "  - To be filled"
    author_line = ", ".join(authors) if authors else "To be filled"
    created = args.created or date.today().isoformat()
    pdf = args.pdf or "To be filled"
    title = args.title
    year = args.year or ""

    return f"""---
source_type: zotero_paper
title: "{title}"
authors:
{author_yaml}
year: {year}
venue: ""
arxiv: ""
url: ""
collections:
  - ""
tags:
  - raw
  - zotero
  - paper
reading_status: not-read
summary_status: pending_full_text
created: {created}
---

# {title}

## Zotero Metadata

- **Title:** {title}
- **Authors:** {author_line}
- **Year:** {year or "To be filled"}
- **Venue:** To be filled
- **arXiv:** To be filled
- **Project page:** To be filled
- **Collection path:** To be filled

## PDF Source

- **External PDF path:** `{pdf}`
- **Important rule:** This raw seed note records the source path only. Do not move, copy, delete, or rewrite the original Zotero PDF.

## Source Availability

- The paper PDF availability should be verified before full summarization.
- Code/data/checkpoint release status: To be filled.

## AI-Generated Initial Summary

To be filled from the full paper PDF.

## Required Questions

### 1. What problem does it solve?

### 2. How does it solve the problem?

### 3. What are the key findings?

### 4. Why is this important?

## My Reading Notes

To be filled after personal reading.

## Later Wiki Update Targets

- `wiki/papers/{title}.md`
- `wiki/methods/METHOD.md`
- `wiki/concepts/CONCEPT.md`
- `wiki/tasks/TASK.md`
- `wiki/experiments/METHOD Reproduction Plan.md`

## Open Questions

- What should be checked during personal reading?
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True)
    parser.add_argument("--year", default="")
    parser.add_argument("--authors", default="")
    parser.add_argument("--pdf", default="")
    parser.add_argument("--created", default="")
    parser.add_argument("--out-dir", default="raw/papers")
    parser.add_argument("--dry-run", action="store_true", help="Print target path and note text without writing.")
    args = parser.parse_args()

    filename = f"{args.year + ' - ' if args.year else ''}{sanitize_filename(args.title)}.md"
    target = Path(args.out_dir) / filename
    text = note_text(args)

    if args.dry_run:
        print(f"TARGET: {target}")
        print()
        print(text)
        return 0

    if target.exists():
        raise SystemExit(f"Refusing to overwrite existing seed note: {target}")

    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    print(target)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

