# src/usb_pd_parser.py
"""
End-to-end runner: reads data/usb_pd_parser.pdf and writes:
 - data/usb_pd_toc.jsonl
 - data/usb_pd_content.jsonl
"""

import os
import json

print("Script started...")

# Correct imports (must use src.<package>)
from src.core.adapter.pymupdf_adapter import PyMuPDFAdapter
from src.parsers.full_pdf_parser import FullPDFParser
from src.extractors.toc_extractor import ToCExtractor
from src.extractors.chunk_extractor import ChunkExtractor


def write_jsonl(path, items):
    """Write list of dictionaries into JSONL format."""
    with open(path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


def main():
    # PDF file expected under /data/
    pdf_path = os.path.join("data", "usb_pd_parser.pdf")

    if not os.path.exists(pdf_path):
        print("PDF not found:", pdf_path)
        return

    # 1) Extract pages using strategy (PyMuPDF)
    strategy = PyMuPDFAdapter()
    parser = FullPDFParser(strategy)
    parser.pdf_path = pdf_path

    pages = parser.parse()  # [{"page_number": int, "text": str}, ...]
    print(f"Loaded {len(pages)} pages from PDF")

    # 2) Extract Table of Contents
    toc_extractor = ToCExtractor()
    toc = toc_extractor.extract(pages)
    print(f"Detected {len(toc)} ToC entries")

    # 3) Extract content chunks mapped to ToC
    chunk_extractor = ChunkExtractor()
    chunks = chunk_extractor.extract(pages, toc)
    print(f"Built {len(chunks)} content chunks")

    # Ensure output folder exists
    os.makedirs("data", exist_ok=True)

    toc_out = os.path.join("data", "usb_pd_toc.jsonl")
    content_out = os.path.join("data", "usb_pd_content.jsonl")

    # 4) Save results
    write_jsonl(toc_out, toc)
    write_jsonl(content_out, chunks)

    print("Wrote:", toc_out, content_out)
    print("Script finished!")


if __name__ == "__main__":
    main()
