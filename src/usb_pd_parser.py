"""
USB PD Specification – End-to-End Parser (High-Fidelity + OOP)

Pipeline:
    1. Extract pages using HighFidelityExtractor (OCR + blocks)
    2. Extract Table of Contents (navigation only)
    3. Extract inline numeric headings (authoritative)
    4. Build spec sections from inline headings
    5. Save:
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
from src.extractors.toc_extractor import ToCExtractor
from src.extractors.inline_heading_extractor import (
    InlineHeadingExtractor,
)
from src.extractors.section_builder import (
    SectionContentBuilder,
)

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
    """Write a list of dictionaries into a JSONL file."""
    with path.open("w", encoding="utf-8") as f:
        for obj in items:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


# ------------------------------------------------------------------
# Main Orchestrator
# ------------------------------------------------------------------
class USBPDParser:
    """
    Coordinates the USB PD PDF parsing pipeline.
    """

    DOC_TITLE = "USB Power Delivery Specification Rev X"

    def __init__(self, pdf_path: str, output_dir: str = "data"):
        self._pdf_path = Path(pdf_path)
        self._output_dir = Path(output_dir)

        self._page_extractor = HighFidelityExtractor()
        self._toc_extractor = ToCExtractor()
        self._inline_extractor = InlineHeadingExtractor()
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
            logger.error("No pages extracted from PDF.")
            return

        logger.info("Extracted %d pages.", len(pages))

        # Wrap pages for extractors expecting pdf_data
        pdf_data = {"pages": pages}

        # ----------------------------------------------------------
        # 2. Extract TOC (navigation only)
        # ----------------------------------------------------------
        toc = self._toc_extractor.extract(pages)
        logger.info("Extracted %d TOC entries.", len(toc))

        # ----------------------------------------------------------
        # 3. Extract inline numeric headings (AUTHORITATIVE)
        # ----------------------------------------------------------
        inline_headings = self._inline_extractor.extract(pdf_data)
        logger.info(
            "Extracted %d numeric section headings.",
            len(inline_headings),
        )

        # ----------------------------------------------------------
        # 4. Build spec sections from numeric headings only
        # ----------------------------------------------------------
        sections = self._section_builder.build(
            toc=toc,
            pages=pages,
            headings=inline_headings,
            doc_title=self.DOC_TITLE,
        )

        logger.info(
            "Built %d spec sections.", len(sections)
        )

        # ----------------------------------------------------------
        # 5. Ensure output directory exists
        # ----------------------------------------------------------
        self._output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        toc_path = self._output_dir / "usb_pd_toc.jsonl"
        spec_path = self._output_dir / "usb_pd_spec.jsonl"

        # ----------------------------------------------------------
        # 6. Save JSONL outputs
        # ----------------------------------------------------------
        write_jsonl(toc_path, toc)
        write_jsonl(spec_path, sections)

        logger.info("TOC saved at: %s", toc_path)
        logger.info("Spec saved at: %s", spec_path)
        logger.info("USB PD Parsing completed successfully.")

        return {
            "pages_extracted": len(pages),
            "toc_entries": len(toc),
            "inline_headings": len(inline_headings),
            "sections_built": len(sections),
            "toc_path": str(toc_path),
            "spec_path": str(spec_path),
        }


# ------------------------------------------------------------------
# CLI Entry Point
# ------------------------------------------------------------------
def main():
    """CLI entry point for USB PD Parser."""
    parser = argparse.ArgumentParser(
        description="USB PD Specification PDF Parser"
    )

    parser.add_argument(
        "pdf",
        help="Path to the PDF file to parse",
    )

    parser.add_argument(
        "--output",
        default="data",
        help="Output directory (default: data)",
    )

    args = parser.parse_args()

    runner = USBPDParser(args.pdf, args.output)
    runner.run()


if __name__ == "__main__":
    main()
