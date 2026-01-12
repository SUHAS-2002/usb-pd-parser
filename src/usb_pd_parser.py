"""
USB PD Specification – End-to-End Parser (High-Fidelity + OOP)

Pipeline:
    1. Extract pages using PDFExtractorProtocol
    2. Extract Table of Contents (navigation only)
    3. Extract inline numeric headings (authoritative)
    4. Build spec sections from inline headings
    5. Save:
        data/usb_pd_toc.jsonl
        data/usb_pd_spec.jsonl

Supports:
    - CLI usage (backward compatible)
    - Strategy Pattern
    - Factory Pattern
    - Context Manager
"""

import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any

from src.core.base_parser import BaseParser
from src.core.interfaces import (
    PDFExtractorProtocol,
    ToCExtractorProtocol,
    InlineHeadingExtractorProtocol,
    SectionBuilderProtocol,
)
from src.core.pdf_text_strategy import PDFTextStrategy
from src.core.parser_factory import ParserFactory

from src.extractors.high_fidelity_extractor import HighFidelityExtractor
from src.extractors.toc_extractor import ToCExtractor
from src.extractors.inline_heading_extractor import InlineHeadingExtractor
from src.extractors.section_builder import SectionContentBuilder

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
def write_jsonl(path: Path, items) -> None:
    """Write a list of dictionaries into a JSONL file."""
    with path.open("w", encoding="utf-8") as f:
        for obj in items:
            f.write(json.dumps(obj, ensure_ascii=False) + "\n")


# ------------------------------------------------------------------
# Main Orchestrator
# ------------------------------------------------------------------
class USBPDParser(BaseParser):
    """
    Coordinates the USB PD PDF parsing pipeline.

    Backward compatible with:
        USBPDParser(pdf_path, output_dir)

    Also supports:
        USBPDParser(strategy, pdf_path, output_dir)
    """

    DOC_TITLE = "USB Power Delivery Specification Rev X"

    # --------------------------------------------------------------
    # Constructor (BACKWARD COMPATIBLE)
    # --------------------------------------------------------------
    def __init__(
        self,
        *args,
        pdf_path: str | None = None,
        output_dir: str | Path = "data",
        toc_extractor: ToCExtractorProtocol | None = None,
        inline_extractor: InlineHeadingExtractorProtocol | None = None,
        section_builder: SectionBuilderProtocol | None = None,
        strategy: PDFTextStrategy | None = None,
    ) -> None:
        """
        Supports:
        - USBPDParser(pdf_path, output_dir)              [CLI / legacy]
        - USBPDParser(strategy, pdf_path, output_dir)    [Factory]
        """

        # ------------------------------
        # Detect invocation style
        # ------------------------------
        if args:
            if isinstance(args[0], PDFTextStrategy):
                # Factory-style
                strategy = args[0]
                pdf_path = args[1]
                if len(args) > 2:
                    output_dir = args[2]
            else:
                # CLI / legacy-style
                pdf_path = args[0]
                if len(args) > 1:
                    output_dir = args[1]
                strategy = HighFidelityExtractor()

        if strategy is None:
            strategy = HighFidelityExtractor()

        super().__init__(strategy)

        # Private attributes
        self._output_dir: Path | None = None

        # Validated via setters
        self.pdf_path = pdf_path  # type: ignore[arg-type]
        self.output_dir = output_dir

        # Composition (Dependency Injection ready)
        self._page_extractor: PDFExtractorProtocol = strategy
        self._toc_extractor: ToCExtractorProtocol = (
            toc_extractor or ToCExtractor()
        )
        self._inline_extractor: InlineHeadingExtractorProtocol = (
            inline_extractor or InlineHeadingExtractor()
        )
        self._section_builder: SectionBuilderProtocol = (
            section_builder or SectionContentBuilder()
        )

    # --------------------------------------------------------------
    # Context Manager Support
    # --------------------------------------------------------------
    def __enter__(self) -> "USBPDParser":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False

    # --------------------------------------------------------------
    # Polymorphism
    # --------------------------------------------------------------
    def __str__(self) -> str:
        return f"USBPDParser(pdf={Path(self.pdf_path).name})"

    def __repr__(self) -> str:
        return (
            "USBPDParser("
            f"pdf_path={self.pdf_path!r}, "
            f"output_dir={self.output_dir!r}"
            ")"
        )

    def __len__(self) -> int:
        return 4

    # --------------------------------------------------------------
    # Encapsulation: output_dir (IMPROVEMENT 8)
    # --------------------------------------------------------------
    @property
    def output_dir(self) -> Path:
        """Return output directory path."""
        return self._output_dir or Path("data")

    @output_dir.setter
    def output_dir(self, value: str | Path) -> None:
        """
        Set output directory with validation.

        Ensures directory exists and is a valid Path.
        """
        if isinstance(value, str):
            path = Path(value)
        elif isinstance(value, Path):
            path = value
        else:
            raise ValueError("output_dir must be str or Path")

        path.mkdir(parents=True, exist_ok=True)
        self._output_dir = path

    # --------------------------------------------------------------
    # BaseParser contract
    # --------------------------------------------------------------
    def parse(self) -> Dict[str, Any]:
        logger.info("Starting USB PD Parser...")
        logger.info("Reading PDF: %s", self.pdf_path)

        # 1. Extract pages
        pages = self._page_extractor.extract(self.pdf_path)
        if not pages:
            logger.error("No pages extracted from PDF.")
            return {}

        logger.info("Extracted %d pages.", len(pages))
        pdf_data = {"pages": pages}

        # 2. Extract TOC
        toc = self._toc_extractor.extract(pages)
        logger.info("Extracted %d TOC entries.", len(toc))

        # 3. Extract inline numeric headings
        inline_headings = self._inline_extractor.extract(pdf_data)
        logger.info(
            "Extracted %d numeric section headings.",
            len(inline_headings),
        )

        # 4. Build sections
        sections = self._section_builder.build(
            toc=toc,
            pages=pages,
            headings=inline_headings,
            doc_title=self.DOC_TITLE,
        )

        logger.info("Built %d spec sections.", len(sections))

        # 5. Save outputs
        toc_path = self.output_dir / "usb_pd_toc.jsonl"
        spec_path = self.output_dir / "usb_pd_spec.jsonl"

        write_jsonl(toc_path, toc)
        write_jsonl(spec_path, sections)

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
# Factory registration
# ------------------------------------------------------------------
ParserFactory.register("usb_pd", USBPDParser)


# ------------------------------------------------------------------
# CLI Entry Point (UNCHANGED)
# ------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="USB PD Specification PDF Parser"
    )
    parser.add_argument("pdf", help="Path to the PDF file to parse")
    parser.add_argument(
        "--output",
        default="data",
        help="Output directory (default: data)",
    )

    args = parser.parse_args()

    USBPDParser(args.pdf, args.output).run()


if __name__ == "__main__":
    main()
