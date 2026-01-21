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
"""

from __future__ import annotations

import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, Iterable, Tuple

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
_logger = logging.getLogger(__name__)


# ------------------------------------------------------------------
# JSONL writer (internal utility)
# ------------------------------------------------------------------
def _write_jsonl(path: Path, items: Iterable[dict]) -> None:
    """Write iterable of dictionaries to a JSONL file."""
    with path.open("w", encoding="utf-8") as handle:
        for obj in items:
            handle.write(json.dumps(obj, ensure_ascii=False) + "\n")


# ------------------------------------------------------------------
# Main Orchestrator
# ------------------------------------------------------------------
class USBPDParser(BaseParser):
    """
    Coordinates the USB PD PDF parsing pipeline.

    Encapsulation rules:
    - ALL internal state uses name-mangled private attributes (__attr)
    - External access only via properties
    - Workflow decomposed into protected methods
    """

    DOC_TITLE: str = "USB Power Delivery Specification Rev X"

    # --------------------------------------------------------------
    # Constructor (AGGRESSIVE ENCAPSULATION)
    # --------------------------------------------------------------
    def __init__(
        self,
        *args: Any,
        pdf_path: str | None = None,
        output_dir: str | Path = "data",
        toc_extractor: ToCExtractorProtocol | None = None,
        inline_extractor: InlineHeadingExtractorProtocol | None = None,
        section_builder: SectionBuilderProtocol | None = None,
        strategy: PDFTextStrategy | None = None,
    ) -> None:
        """
        Supported invocation styles:
        - USBPDParser(pdf_path, output_dir)
        - USBPDParser(strategy, pdf_path, output_dir)
        """

        strategy, pdf_path, output_dir = self._parse_args(
            args, strategy, pdf_path, output_dir
        )

        super().__init__(strategy)

        self.__initialize_state()

        if pdf_path is not None:
            self.pdf_path = pdf_path
        self.output_dir = output_dir

        self.__initialize_dependencies(
            toc_extractor,
            inline_extractor,
            section_builder,
            strategy,
        )

    # --------------------------------------------------------------
    # Argument normalization (protected)
    # --------------------------------------------------------------
    def _parse_args(
        self,
        args: tuple[Any, ...],
        strategy: PDFTextStrategy | None,
        pdf_path: str | None,
        output_dir: str | Path,
    ) -> Tuple[PDFTextStrategy, str | None, str | Path]:
        if args:
            if isinstance(args[0], PDFTextStrategy):
                return (
                    args[0],
                    args[1] if len(args) > 1 else pdf_path,
                    args[2] if len(args) > 2 else output_dir,
                )

            return (
                HighFidelityExtractor(),
                args[0],
                args[1] if len(args) > 1 else output_dir,
            )

        return (
            strategy or HighFidelityExtractor(),
            pdf_path,
            output_dir,
        )

    # --------------------------------------------------------------
    # Private state initialization (TRUE PRIVATE)
    # --------------------------------------------------------------
    def __initialize_state(self) -> None:
        self.__output_dir: Path | None = None
        self.__page_extractor: PDFExtractorProtocol | None = None
        self.__toc_extractor: ToCExtractorProtocol | None = None
        self.__inline_extractor: InlineHeadingExtractorProtocol | None = None
        self.__section_builder: SectionBuilderProtocol | None = None

        self.__pages: list[dict] | None = None
        self.__toc: list[dict] | None = None
        self.__headings: list[dict] | None = None
        self.__sections: list[dict] | None = None

    # --------------------------------------------------------------
    # Dependency wiring (private)
    # --------------------------------------------------------------
    def __initialize_dependencies(
        self,
        toc_extractor: ToCExtractorProtocol | None,
        inline_extractor: InlineHeadingExtractorProtocol | None,
        section_builder: SectionBuilderProtocol | None,
        strategy: PDFTextStrategy,
    ) -> None:
        self.__page_extractor = strategy
        self.__toc_extractor = toc_extractor or ToCExtractor()
        self.__inline_extractor = inline_extractor or InlineHeadingExtractor()
        self.__section_builder = section_builder or SectionContentBuilder()

    # --------------------------------------------------------------
    # Context manager
    # --------------------------------------------------------------
    def __enter__(self) -> "USBPDParser":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False

    # --------------------------------------------------------------
    # Dunder methods
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
    # Encapsulation: output_dir (controlled access)
    # --------------------------------------------------------------
    @property
    def output_dir(self) -> Path:
        return self.__output_dir or Path("data")

    @output_dir.setter
    def output_dir(self, value: str | Path) -> None:
        path = Path(value)
        path.mkdir(parents=True, exist_ok=True)
        self.__output_dir = path

    # --------------------------------------------------------------
    # Read-only dependency accessors
    # --------------------------------------------------------------
    @property
    def page_extractor(self) -> PDFExtractorProtocol:
        if self.__page_extractor is None:
            raise RuntimeError("Page extractor not initialized")
        return self.__page_extractor

    @property
    def toc_extractor(self) -> ToCExtractorProtocol:
        if self.__toc_extractor is None:
            raise RuntimeError("ToC extractor not initialized")
        return self.__toc_extractor

    @property
    def inline_extractor(self) -> InlineHeadingExtractorProtocol:
        if self.__inline_extractor is None:
            raise RuntimeError("Inline extractor not initialized")
        return self.__inline_extractor

    @property
    def section_builder(self) -> SectionBuilderProtocol:
        if self.__section_builder is None:
            raise RuntimeError("Section builder not initialized")
        return self.__section_builder

    # --------------------------------------------------------------
    # BaseParser contract
    # --------------------------------------------------------------
    def parse(self) -> Dict[str, Any]:
        _logger.info("Starting USB PD parsing pipeline")

        pages = self._extract_pages()
        toc = self._extract_toc(pages)
        headings = self._extract_inline_headings(pages)
        sections = self._build_sections(pages, toc, headings)

        self._persist_outputs(toc, sections)

        _logger.info("USB PD parsing completed successfully")

        return {
            "pages_extracted": len(pages),
            "toc_entries": len(toc),
            "inline_headings": len(headings),
            "sections_built": len(sections),
            "output_dir": str(self.output_dir),
        }

    # --------------------------------------------------------------
    # Pipeline steps (protected)
    # --------------------------------------------------------------
    def _extract_pages(self) -> list[dict]:
        _logger.info("Extracting pages from PDF: %s", self.pdf_path)
        pages = self.page_extractor.extract(self.pdf_path)
        if not pages:
            raise RuntimeError("No pages extracted from PDF")
        self.__pages = pages
        return pages

    def _extract_toc(self, pages: list[dict]) -> list[dict]:
        toc = self.toc_extractor.extract(pages)
        _logger.info("Extracted %d TOC entries", len(toc))
        self.__toc = toc
        return toc

    def _extract_inline_headings(self, pages: list[dict]) -> list[dict]:
        data = {"pages": pages}
        headings = self.inline_extractor.extract(data)
        _logger.info("Extracted %d inline headings", len(headings))
        self.__headings = headings
        return headings

    def _build_sections(
        self,
        pages: list[dict],
        toc: list[dict],
        headings: list[dict],
    ) -> list[dict]:
        sections = self.section_builder.build(
            toc=toc,
            pages=pages,
            headings=headings,
            doc_title=self.DOC_TITLE,
        )
        _logger.info("Built %d spec sections", len(sections))
        self.__sections = sections
        return sections

    def _persist_outputs(
        self,
        toc: list[dict],
        sections: list[dict],
    ) -> None:
        _write_jsonl(self.output_dir / "usb_pd_toc.jsonl", toc)
        _write_jsonl(self.output_dir / "usb_pd_spec.jsonl", sections)


# ------------------------------------------------------------------
# Factory registration
# ------------------------------------------------------------------
ParserFactory.register("usb_pd", USBPDParser)


# ------------------------------------------------------------------
# CLI entry point (UNCHANGED)
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
