# src/usb_pd_parser.py
"""
USB PD Specification – End-to-End Parser

This script:
  1. Reads the PDF (data/usb_pd_parser.pdf)
  2. Extracts all pages (gap-free, normalized)
  3. Extracts TOC entries
  4. Extracts content chunks mapped to TOC
  5. Saves:
        • data/usb_pd_toc.jsonl
        • data/usb_pd_content.jsonl
"""

import os
import json
import logging
from pathlib import Path

# Correct imports
from src.core.adapter.pymupdf_adapter import PyMuPDFAdapter
from src.parsers.full_pdf_parser import FullPDFParser
from src.extractors.toc_extractor import ToCExtractor
from src.extractors.chunk_extractor import ChunkExtractor


# ------------------------------------------------------------
# Logging
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# Helper function: write JSONL
# ------------------------------------------------------------
def write_jsonl(path, items):
    """Write list of dictionaries into JSONL format."""
    with open(path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


# ------------------------------------------------------------
# Main Parser Orchestrator
# ------------------------------------------------------------
class USBPDParser:
    """
    High-level orchestrator for parsing the USB PD spec PDF.
    Clean OOP design:
        - Strategy pattern for PDF extraction
        - Separate extractors for TOC and chunks
        - Validated outputs
    """

    def __init__(self, pdf_path: str, out_dir: str = "data"):
        self.pdf_path = pdf_path
        self.out_dir = Path(out_dir)

        self.strategy = PyMuPDFAdapter()
        self.page_parser = FullPDFParser(self.strategy)
        self.toc_extractor = ToCExtractor()
        self.chunk_extractor = ChunkExtractor()

    # --------------------------------------------------------
    def run(self):
        logger.info("Starting USB PD Parser…")
        logger.info(f"Reading PDF: {self.pdf_path}")

        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF not found: {self.pdf_path}")

        # 1) Load pages
        self.page_parser.pdf_path = self.pdf_path
        pages = self.page_parser.parse()

        if not pages:
            logger.error("No pages extracted from PDF.")
            return

        logger.info(f"Loaded {len(pages)} normalized pages")

        # 2) Extract ToC
        toc = self.toc_extractor.extract(pages)
        if not toc:
            logger.warning("No TOC entries detected.")
        else:
            logger.info(f"Extracted {len(toc)} TOC entries")

        # 3) Extract content chunks
        chunks = self.chunk_extractor.extract(pages, toc)
        logger.info(f"Built {len(chunks)} content chunks")

        # 4) Prepare output directory
        self.out_dir.mkdir(parents=True, exist_ok=True)

        toc_path = self.out_dir / "usb_pd_toc.jsonl"
        chunks_path = self.out_dir / "usb_pd_content.jsonl"

        # 5) Save JSONL results
        write_jsonl(toc_path, toc)
        write_jsonl(chunks_path, chunks)

        logger.info(f"Saved TOC to: {toc_path}")
        logger.info(f"Saved Content Chunks to: {chunks_path}")
        logger.info("USB PD Parsing Completed Successfully!")


# ------------------------------------------------------------
# CLI entrypoint
# ------------------------------------------------------------
def main():
    pdf_path = os.path.join("data", "usb_pd_parser.pdf")
    parser = USBPDParser(pdf_path=pdf_path)
    parser.run()


if __name__ == "__main__":
    main()
