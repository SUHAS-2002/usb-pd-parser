"""
Extract ALL pages from a PDF using HighFidelityExtractor.

This script is ONLY for debugging page extraction.
It does NOT extract TOC or sections.
"""

import json
from pathlib import Path
from src.extractors.high_fidelity_extractor import HighFidelityExtractor


def write_jsonl(path: Path, items):
    """Write list of dictionaries to JSONL."""
    with path.open("w", encoding="utf-8") as f:
        for obj in items:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def extract_all_pages(pdf_path: str, output: str = "data/all_pages.jsonl"):
    extractor = HighFidelityExtractor()

    print(f"Extracting pages from: {pdf_path}")
    pages = extractor.extract(pdf_path)

    if not pages:
        print("ERROR: No pages extracted.")
        return

    print(f"Extracted {len(pages)} pages.")

    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    write_jsonl(output_path, pages)

    print(f"Saved → {output_path}")
    return output_path


if __name__ == "__main__":
    pdf = "data/usb_pd_parser.pdf"
    extract_all_pages(pdf)
