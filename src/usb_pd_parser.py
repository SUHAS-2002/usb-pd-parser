# src/usb_pd_parser.py
"""
End-to-end runner: reads data/usb_pd_parser.pdf and writes:
 - data/usb_pd_toc.jsonl
 - data/usb_pd_content.jsonl
"""

import os
import json
print("Script started...")

from src.core.adapter.pymupdf_adapter import PyMuPDFAdapter
from parsers.full_pdf_parser import FullPDFParser
from extractors.toc_extractor import ToCExtractor
from extractors.chunk_extractor import ChunkExtractor

def write_jsonl(path, items):
    with open(path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

def main():
    pdf_path = os.path.join("data", "usb_pd_parser.pdf")
    if not os.path.exists(pdf_path):
        print("PDF not found:", pdf_path)
        return

    # 1) read pages
    strategy = PyMuPDFAdapter()
    parser = FullPDFParser(strategy)
    parser.pdf_path = pdf_path
    pages = parser.parse()  # list of {"page_number","text"}
    print(f"Loaded {len(pages)} pages from PDF")

    # 2) extract ToC (full-doc scan and front-matter)
    toc_extractor = ToCExtractor()
    toc = toc_extractor.extract(pages)
    print(f"Detected {len(toc)} ToC entries")

    # 3) build chunks mapped to ToC
    chunk_extractor = ChunkExtractor()
    chunks = chunk_extractor.extract(pages, toc)
    print(f"Built {len(chunks)} content chunks")

    # 4) write outputs under data/
    os.makedirs("data", exist_ok=True)
    toc_out = os.path.join("data", "usb_pd_toc.jsonl")
    content_out = os.path.join("data", "usb_pd_content.jsonl")
    write_jsonl(toc_out, toc)
    write_jsonl(content_out, chunks)

    print("Wrote:", toc_out, content_out)

if __name__ == "__main__":
    main()
    print("Script finished!")
