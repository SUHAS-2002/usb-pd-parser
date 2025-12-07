"""
USB PD Specification – End-to-End Parser (High-Fidelity + OOP)

Pipeline:
    1. Extract pages using HighFidelityExtractor (OCR + blocks)
    2. Extract the Table of Contents
    3. Build section content using TOC page boundaries
    4. Save:
        data/usb_pd_toc.jsonl
        data/usb_pd_spec.jsonl
"""

import json
import argparse
import logging
from pathlib import Path

from src.extractors.high_fidelity_extractor import (
    HighFidelityExtractor,
)
from src.extractors.section_builder import (
    SectionContentBuilder,
)
from src.extractors.toc_extractor import ToCExtractor


# ------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# JSONL writer
# ------------------------------------------------------------------
def write_jsonl(path: Path, items):
    """
    Write a list of dictionaries into a JSONL file.
    """
    with path.open("w", encoding="utf-8") as f:
        for obj in items:
            line = json.dumps(obj, ensure_ascii=False)
            f.write(line + "\n")


# ------------------------------------------------------------------
# Main Orchestrator
# ------------------------------------------------------------------
class USBPDParser:
    """
    Coordinates the USB PD PDF parsing pipeline.

    Components:
        - HighFidelityExtractor : extracts page text
        - ToCExtractor          : extracts TOC entries
        - SectionContentBuilder : builds section content blocks
    """

    def __init__(self, pdf_path: str, output_dir: str = "data"):
        self._pdf_path = Path(pdf_path)
        self._output_dir = Path(output_dir)

        self._page_extractor = HighFidelityExtractor()
        self._toc_extractor = ToCExtractor()
        self._section_builder = SectionContentBuilder()

    # --------------------------------------------------------------
    def run(self):
        """Run the complete parsing pipeline."""
        logger.info("Starting USB PD Parser...")
        logger.info("Reading PDF: %s", self._pdf_path)

        if not self._pdf_path.exists():
            raise FileNotFoundError(
                f"PDF not found: {self._pdf_path}"
            )

        # ----------------------------------------------------------
        # 1. Extract pages
        # ----------------------------------------------------------
        pages = self._page_extractor.extract(str(self._pdf_path))

        if not pages:
            logger.error(
                "Page extraction failed: zero pages extracted."
            )
            return

        logger.info("Extracted %d pages.", len(pages))

        # ----------------------------------------------------------
        # 2. Extract TOC
        # ----------------------------------------------------------
        toc = self._toc_extractor.extract(pages)

        if toc:
            logger.info("Extracted %d TOC entries.", len(toc))
        else:
            logger.warning("No TOC entries extracted.")

        # ----------------------------------------------------------
        # 3. Build section content blocks
        # ----------------------------------------------------------
        sections = self._section_builder.build(toc, pages)
        logger.info(
            "Built %d section content blocks.", len(sections)
        )

        # ----------------------------------------------------------
        # 4. Ensure output directory exists
        # ----------------------------------------------------------
        self._output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        toc_path = self._output_dir / "usb_pd_toc.jsonl"
        content_path = self._output_dir / "usb_pd_spec.jsonl"

        # ----------------------------------------------------------
        # 5. Save JSONL outputs
        # ----------------------------------------------------------
        write_jsonl(toc_path, toc)
        write_jsonl(content_path, sections)

        logger.info("TOC saved at: %s", toc_path)
        logger.info("Content saved at: %s", content_path)
        logger.info("USB PD Parsing completed successfully.")

        return {
            "pages_extracted": len(pages),
            "toc_entries": len(toc),
            "sections_built": len(sections),
            "toc_path": str(toc_path),
            "content_path": str(content_path),
        }


# ------------------------------------------------------------------
# CLI Entry Point
# ------------------------------------------------------------------
def main():
    """
    CLI entry point for USB PD Parser.
    Allows providing custom PDF path and output directory.
    """
    parser = argparse.ArgumentParser(
        description="USB PD Specification PDF Parser"
    )

    parser.add_argument(
        "pdf",
        help="Path to the PDF file to parse"
    )

    parser.add_argument(
        "--output",
        default="data",
        help="Output directory for JSONL files (default: data)"
    )

    args = parser.parse_args()

    runner = USBPDParser(args.pdf, args.output)
    runner.run()


if __name__ == "__main__":
    main()
