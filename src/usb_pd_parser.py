"""
USB PD Specification – End-to-End Parser (High-Fidelity + OOP)

Pipeline:
    1. Extract all pages using HighFidelityExtractor (OCR + block text)
    2. Extract the TOC
    3. Build section content using TOC page boundaries
    4. Save:
         data/usb_pd_toc.jsonl
         data/usb_pd_spec.jsonl
"""

import os
import json
import logging
from pathlib import Path

from src.extractors.high_fidelity_extractor import HighFidelityExtractor
from src.extractors.section_builder import SectionContentBuilder
from src.extractors.toc_extractor import ToCExtractor


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# JSONL writer
# ---------------------------------------------------------------------------
def write_jsonl(path: Path, items):
    """Write a list of dicts into a JSONL file."""
    with path.open("w", encoding="utf-8") as f:
        for obj in items:
            line = json.dumps(obj, ensure_ascii=False)
            f.write(line + "\n")


# ---------------------------------------------------------------------------
# Main Orchestrator
# ---------------------------------------------------------------------------
class USBPDParser:
    """
    Coordinates the full USB PD PDF parsing pipeline.

    Components used:
        - HighFidelityExtractor  → extract page text
        - ToCExtractor           → extract table of contents entries
        - SectionContentBuilder  → build section-based content blocks
    """

    def __init__(self, pdf_path: str, output_dir: str = "data"):
        self._pdf_path = Path(pdf_path)
        self._output_dir = Path(output_dir)

        self._page_extractor = HighFidelityExtractor()
        self._toc_extractor = ToCExtractor()
        self._section_builder = SectionContentBuilder()

    # -----------------------------------------------------------------------
    def run(self):
        """Run the complete parsing pipeline."""
        logger.info("Starting USB PD Parser…")
        logger.info("Reading PDF → %s", self._pdf_path)

        if not self._pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {self._pdf_path}")

        # -------------------------------------------------------------------
        # 1. Extract all pages
        # -------------------------------------------------------------------
        pages = self._page_extractor.extract(str(self._pdf_path))
        if not pages:
            logger.error("Page extraction failed — zero pages extracted.")
            return

        logger.info("Extracted %d pages.", len(pages))

        # -------------------------------------------------------------------
        # 2. Extract TOC
        # -------------------------------------------------------------------
        toc = self._toc_extractor.extract(pages)
        if toc:
            logger.info("Extracted %d TOC entries.", len(toc))
        else:
            logger.warning("No TOC entries extracted.")

        # -------------------------------------------------------------------
        # 3. Build section content blocks
        # -------------------------------------------------------------------
        sections = self._section_builder.build(toc, pages)
        logger.info("Built %d section content blocks.", len(sections))

        # -------------------------------------------------------------------
        # 4. Ensure output directory
        # -------------------------------------------------------------------
        self._output_dir.mkdir(parents=True, exist_ok=True)

        toc_path = self._output_dir / "usb_pd_toc.jsonl"
        content_path = self._output_dir / "usb_pd_spec.jsonl"

        # -------------------------------------------------------------------
        # 5. Save results
        # -------------------------------------------------------------------
        write_jsonl(toc_path, toc)
        write_jsonl(content_path, sections)

        logger.info("TOC saved → %s", toc_path)
        logger.info("Content saved → %s", content_path)
        logger.info("USB PD Parsing Completed Successfully.")

        return {
            "pages_extracted": len(pages),
            "toc_entries": len(toc),
            "sections_built": len(sections),
            "toc_path": str(toc_path),
            "content_path": str(content_path),
        }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    """Default CLI entry point."""
    pdf_path = os.path.join("data", "usb_pd_parser.pdf")
    parser = USBPDParser(pdf_path)
    parser.run()


if __name__ == "__main__":
    main()
