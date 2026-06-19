#!/usr/bin/env python3
"""Extract text from a PDF for paper-ingest planning and summarization."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", help="PDF path to read.")
    parser.add_argument("--pages", type=int, default=0, help="Maximum pages to extract; 0 means all pages.")
    parser.add_argument("--start-page", type=int, default=1, help="1-based first page to extract.")
    args = parser.parse_args()

    pdf_path = Path(args.pdf).expanduser()
    if not pdf_path.exists():
        raise SystemExit(f"PDF does not exist: {pdf_path}")

    try:
        import pdfplumber
    except ImportError as exc:
        raise SystemExit("Missing dependency: pdfplumber. Use the vault .venv or install pdfplumber.") from exc

    with pdfplumber.open(str(pdf_path)) as pdf:
        start = max(args.start_page, 1) - 1
        end = len(pdf.pages) if args.pages <= 0 else min(len(pdf.pages), start + args.pages)
        for idx in range(start, end):
            text = pdf.pages[idx].extract_text() or ""
            print(f"\n\n--- PAGE {idx + 1} ---\n")
            print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

