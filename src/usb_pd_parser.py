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
from src.core.observer_pattern import Observable, Observer

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
    """
    Write iterable of dictionaries to a JSONL file.
    
    Parameters
    ----------
    path : Path
        Output file path
    items : Iterable[dict]
        Items to write (will be iterated once)
    
    Raises
    ------
    OSError
        If file cannot be written
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as handle:
            for obj in items:
                handle.write(json.dumps(obj, ensure_ascii=False) + "\n")
    except OSError as e:
        _logger.error("Failed to write JSONL file %s: %s", path, e)
        raise


# ------------------------------------------------------------------
# Main Orchestrator
# ------------------------------------------------------------------
class USBPDParser(BaseParser, Observable):
    """
    Coordinates the USB PD PDF parsing pipeline.

    Encapsulation rules:
    - ALL internal state uses name-mangled private attributes (__attr)
    - External access only via properties
    - Workflow decomposed into protected methods
    
    Design Patterns:
    - Observer Pattern: Notifies observers about parsing events
    """

    # --------------------------------------------------------------
    # TRUE PRIVATE class constant (encapsulation)
    # --------------------------------------------------------------
    __DOC_TITLE: str = "USB Power Delivery Specification Rev X"

    @classmethod
    def _get_doc_title(cls) -> str:
        """Get document title (protected class method)."""
        return cls.__DOC_TITLE

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

        BaseParser.__init__(self, strategy)
        Observable.__init__(self)  # Initialize Observer pattern

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
    # Read-only data accessors (encapsulation)
    # --------------------------------------------------------------
    @property
    def pages(self) -> list[dict] | None:
        """Get extracted pages (read-only)."""
        return self.__pages.copy() if self.__pages else None

    @property
    def toc(self) -> list[dict] | None:
        """Get extracted TOC entries (read-only)."""
        return self.__toc.copy() if self.__toc else None

    @property
    def headings(self) -> list[dict] | None:
        """Get extracted inline headings (read-only)."""
        return self.__headings.copy() if self.__headings else None

    @property
    def sections(self) -> list[dict] | None:
        """Get built sections (read-only)."""
        return self.__sections.copy() if self.__sections else None

    # --------------------------------------------------------------
    # BaseParser contract
    # --------------------------------------------------------------
    def parse(self) -> Dict[str, Any]:
        _logger.info("Starting USB PD parsing pipeline")
        self.notify("parse_started", {"pdf_path": self.pdf_path})

        pages = self._extract_pages()
        self.notify("pages_extracted", {"count": len(pages)})
        
        toc = self._extract_toc(pages)
        self.notify("toc_extracted", {"count": len(toc)})
        
        headings = self._extract_inline_headings(pages)
        self.notify("headings_extracted", {"count": len(headings)})
        
        sections = self._build_sections(pages, toc, headings)
        self.notify("sections_built", {"count": len(sections)})

        self._persist_outputs(toc, sections)
        self.notify("outputs_persisted", {"output_dir": str(self.output_dir)})

        _logger.info("USB PD parsing completed successfully")
        self.notify("parse_completed", {"success": True})

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
            doc_title=self._get_doc_title(),
        )
        _logger.info("Built %d spec sections", len(sections))
        
        # Log content statistics
        sections_with_content = sum(
            1 for s in sections
            if s.get("content") and len(s.get("content", "").strip()) > 0
        )
        if sections_with_content > 0:
            content_lengths = [
                len(s.get("content", ""))
                for s in sections if s.get("content")
            ]
            avg_content = sum(content_lengths) // len(content_lengths)
            _logger.info(
                "Content statistics: %d sections with content, "
                "avg length: %d chars",
                sections_with_content,
                avg_content
            )
        
        self.__sections = sections
        return sections

    def _persist_outputs(
        self,
        toc: list[dict],
        sections: list[dict],
    ) -> None:
        """Persist all output files."""
        self._write_core_outputs(toc, sections)
        self._generate_content_file(sections)
        self._generate_metadata()
        self._generate_validation_reports()
        self._validate_output_schemas()
        self._generate_summary_output(toc, sections)
    
    def _write_core_outputs(
        self,
        toc: list[dict],
        sections: list[dict],
    ) -> None:
        """Write core TOC and spec files."""
        _write_jsonl(self.output_dir / "usb_pd_toc.jsonl", toc)
        _write_jsonl(self.output_dir / "usb_pd_spec.jsonl", sections)
        _logger.info(
            "Output files generated: TOC=%d entries, "
            "Spec=%d sections",
            len(toc),
            len(sections)
        )
    
    def _generate_content_file(self, sections: list[dict]) -> None:
        """Generate content-only JSONL file."""
        content_sections = [
            s for s in sections
            if s.get("content") and len(s.get("content", "").strip()) > 0
        ]
        content_path = self.output_dir / "usb_pd_content.jsonl"
        _write_jsonl(content_path, content_sections)
    
    def _generate_metadata(self) -> None:
        """Generate metadata JSONL file."""
        from src.generators.metadata_generator import MetadataGenerator
        
        metadata_gen = MetadataGenerator()
        metadata_path = self.output_dir / "usb_pd_metadata.jsonl"
        toc_path = self.output_dir / "usb_pd_toc.jsonl"
        spec_path = self.output_dir / "usb_pd_spec.jsonl"
        
        metadata_gen.generate(
            toc_path=str(toc_path),
            chunks_path=str(spec_path),
            output_path=str(metadata_path),
        )
    
    def _generate_validation_reports(self) -> None:
        """Generate validation reports (JSON and Excel)."""
        from src.validator.toc_validator import TOCValidator
        from src.reports.excel_validation_report import ExcelValidationReport
        
        toc_path = self.output_dir / "usb_pd_toc.jsonl"
        spec_path = self.output_dir / "usb_pd_spec.jsonl"
        validation_json_path = self.output_dir / "validation_report.json"
        
        # Generate JSON validation report
        validator = TOCValidator()
        validator.validate(
            toc_path=str(toc_path),
            chunks_path=str(spec_path),
            report_path=str(validation_json_path),
        )
        
        # Generate Excel validation report
        validation_xlsx_path = self.output_dir / "validation_report.xlsx"
        with ExcelValidationReport(
            report_json_path=str(validation_json_path),
            output_xlsx=str(validation_xlsx_path),
        ) as excel_gen:
            excel_gen.generate()
    
    def _validate_output_schemas(self) -> None:
        """Validate generated output files against JSON schemas."""
        from src.utils.schema_validator import SchemaValidator
        from pathlib import Path
        
        validator = SchemaValidator()
        schema_dir = Path(__file__).parent.parent / "schemas"
        toc_schema = schema_dir / "toc_schema.json"
        toc_file = self.output_dir / "usb_pd_toc.jsonl"
        
        if toc_schema.exists() and toc_file.exists():
            is_valid = validator.validate_file(
                toc_file, toc_schema, strict=False
            )
            if is_valid:
                _logger.info(
                    "TOC file validated against schema successfully"
                )
            else:
                _logger.warning(
                    "TOC file validation found %d errors",
                    validator.error_count
                )
    
    def _generate_summary_output(
        self,
        toc: list[dict],
        sections: list[dict],
    ) -> None:
        """Generate output.json summary file."""
        from src.generators.summary_generator import SummaryGenerator
        
        summary_gen = SummaryGenerator()
        output_path = self.output_dir / "output.json"
        
        toc_path = self.output_dir / "usb_pd_toc.jsonl"
        spec_path = self.output_dir / "usb_pd_spec.jsonl"
        content_path = self.output_dir / "usb_pd_content.jsonl"
        metadata_path = self.output_dir / "usb_pd_metadata.jsonl"
        validation_path = self.output_dir / "validation_report.json"
        
        pages_processed = len(self.__pages) if self.__pages else 0
        
        summary_gen.generate(
            toc_path=str(toc_path),
            spec_path=str(spec_path),
            content_path=str(content_path),
            metadata_path=str(metadata_path),
            validation_path=str(validation_path),
            pages_processed=pages_processed,
            output_path=str(output_path),
        )


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
