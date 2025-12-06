"""
USB PD Specification – End-to-End Parser (High-Fidelity + OOP)

This script:
    ✔ Extracts ALL pages using HighFidelityExtractor (OCR + blocks)
    ✔ Extracts the TOC
    ✔ Builds section-based content using TOC page boundaries
    ✔ Saves:
         • data/usb_pd_toc.jsonl
         • data/usb_pd_spec.jsonl
"""

import os
import json
import logging
from pathlib import Path

# ------------------------------------------------------------
# Imports from existing project architecture (CORRECT)
# ------------------------------------------------------------
from src.extractors.high_fidelity_extractor import HighFidelityExtractor
from src.extractors.section_builder import SectionContentBuilder
from src.extractors.toc_extractor import ToCExtractor


# ------------------------------------------------------------
# Logging configuration
# ------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------
# Helper: Write JSONL
# ------------------------------------------------------------
def write_jsonl(path: Path, items):
    """Save list of dicts into JSONL format."""
    with open(path, "w", encoding="utf-8") as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")


# ------------------------------------------------------------
# Main Orchestrator
# ------------------------------------------------------------
class USBPDParser:
    """
    High-level orchestrator for parsing the USB PD spec.
    Uses:
        ✔ HighFidelityExtractor for full PDF extraction
        ✔ TOC Extractor
        ✔ SectionContentBuilder for merging sections
    """

    def __init__(self, pdf_path: str, output_dir: str = "data"):
        self._pdf_path = Path(pdf_path)
        self._output_dir = Path(output_dir)

        # Use your new high-fidelity page extractor
        self._page_extractor = HighFidelityExtractor()

        # Composition extractors
        self._toc_extractor = ToCExtractor()
        self._section_builder = SectionContentBuilder()

    # ----------------------------------------------------------
    def run(self):
        logger.info("Starting USB PD Parser…")
        logger.info(f"Reading PDF → {self._pdf_path}")

        if not self._pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self._pdf_path}")

        # ------------------------------------------------------
        # 1) Extract ALL pages
        # ------------------------------------------------------
        pages = self._page_extractor.extract(str(self._pdf_path))
        if not pages:
            logger.error("❌ Page extraction failed — Zero pages extracted.")
            return

        logger.info(f"Extracted {len(pages)} pages successfully.")

        # ------------------------------------------------------
        # 2) Extract TOC
        # ------------------------------------------------------
        toc = self._toc_extractor.extract(pages)
        if not toc:
            logger.warning("⚠ No TOC entries extracted.")
        else:
            logger.info(f"Extracted {len(toc)} TOC entries.")

        # ------------------------------------------------------
        # 3) Build section-based content
        # ------------------------------------------------------
        sections = self._section_builder.build(toc, pages)
        logger.info(f"Built {len(sections)} section content blocks.")

        # ------------------------------------------------------
        # 4) Output directory
        # ------------------------------------------------------
        self._output_dir.mkdir(parents=True, exist_ok=True)

        toc_path = self._output_dir / "usb_pd_toc.jsonl"
        content_path = self._output_dir / "usb_pd_spec.jsonl"   # ⬅ renamed

        # ------------------------------------------------------
        # 5) Save results
        # ------------------------------------------------------
        write_jsonl(toc_path, toc)
        write_jsonl(content_path, sections)

        logger.info(f"TOC saved → {toc_path}")
        logger.info(f"Content saved → {content_path}")
        logger.info("✅ USB PD Parsing Completed Successfully!")


# ------------------------------------------------------------
# CLI entrypoint
# ------------------------------------------------------------
def main():
    pdf_path = os.path.join("data", "usb_pd_parser.pdf")
    parser = USBPDParser(pdf_path=pdf_path)
    parser.run()


if __name__ == "__main__":
    main()
