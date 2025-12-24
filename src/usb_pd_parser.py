"""
USB PD Specification – End-to-End Parser (High-Fidelity + OOP)

Pipeline:
    1. Extract pages (HighFidelityExtractor)
    2. Extract TOC (navigation only)
    3. Extract inline numeric headings (authoritative)
    4. Build spec sections
    5. Persist JSONL outputs
"""

import json
import logging
from pathlib import Path
from typing import Dict, List

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

# -------------------------------------------------------------
# Logging (module-local, not global CLI responsibility)
# -------------------------------------------------------------
logger = logging.getLogger(__name__)


class USBPDParser:
    """
    Coordinates the USB PD PDF parsing pipeline.

    Encapsulation rules:
    - run() is the ONLY public method
    - all pipeline steps are private
    - filesystem and state are encapsulated
    """

    __DOC_TITLE = "USB Power Delivery Specification Rev X"

    # ---------------------------------------------------------
    # Construction (private state)
    # ---------------------------------------------------------
    def __init__(self, pdf_path: str, output_dir: str = "data"):
        self.__pdf_path = Path(pdf_path)
        self.__output_dir = Path(output_dir)

        self.__page_extractor = HighFidelityExtractor()
        self.__toc_extractor = ToCExtractor()
        self.__inline_extractor = InlineHeadingExtractor()
        self.__section_builder = SectionContentBuilder()

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def run(self) -> Dict[str, int | str]:
        self.__validate_pdf()

        pages = self.__extract_pages()
        toc = self.__extract_toc(pages)
        headings = self.__extract_inline_headings(pages)
        sections = self.__build_sections(
            toc,
            pages,
            headings,
        )

        self.__persist_outputs(toc, sections)

        return self.__build_summary(
            pages,
            toc,
            headings,
            sections,
        )

    # ---------------------------------------------------------
    # Private pipeline steps
    # ---------------------------------------------------------
    def __validate_pdf(self) -> None:
        logger.info("Starting USB PD Parser...")
        logger.info("Reading PDF: %s", self.__pdf_path)

        if not self.__pdf_path.exists():
            raise FileNotFoundError(
                f"PDF not found: {self.__pdf_path}"
            )

    # ---------------------------------------------------------
    def __extract_pages(self) -> List[Dict]:
        pages = self.__page_extractor.extract(
            str(self.__pdf_path)
        )

        if not pages:
            raise RuntimeError(
                "No pages extracted from PDF."
            )

        logger.info("Extracted %d pages.", len(pages))
        return pages

    # ---------------------------------------------------------
    def __extract_toc(self, pages: List[Dict]) -> List[Dict]:
        toc = self.__toc_extractor.extract(pages)
        logger.info("Extracted %d TOC entries.", len(toc))
        return toc

    # ---------------------------------------------------------
    def __extract_inline_headings(
        self,
        pages: List[Dict],
    ) -> List[Dict]:
        pdf_data = {"pages": pages}

        headings = self.__inline_extractor.extract(
            pdf_data
        )

        logger.info(
            "Extracted %d numeric section headings.",
            len(headings),
        )
        return headings

    # ---------------------------------------------------------
    def __build_sections(
        self,
        toc: List[Dict],
        pages: List[Dict],
        headings: List[Dict],
    ) -> List[Dict]:
        sections = self.__section_builder.build(
            toc=toc,
            pages=pages,
            headings=headings,
            doc_title=self.__DOC_TITLE,
        )

        logger.info(
            "Built %d spec sections.",
            len(sections),
        )
        return sections

    # ---------------------------------------------------------
    def __persist_outputs(
        self,
        toc: List[Dict],
        sections: List[Dict],
    ) -> None:
        self.__output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        toc_path = self.__output_dir / "usb_pd_toc.jsonl"
        spec_path = self.__output_dir / "usb_pd_spec.jsonl"

        self.__write_jsonl(toc_path, toc)
        self.__write_jsonl(spec_path, sections)

        logger.info("TOC saved at: %s", toc_path)
        logger.info("Spec saved at: %s", spec_path)
        logger.info(
            "USB PD Parsing completed successfully."
        )

    # ---------------------------------------------------------
    def __write_jsonl(
        self,
        path: Path,
        items: List[Dict],
    ) -> None:
        with path.open("w", encoding="utf-8") as f:
            for obj in items:
                f.write(
                    json.dumps(
                        obj,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

    # ---------------------------------------------------------
    def __build_summary(
        self,
        pages: List[Dict],
        toc: List[Dict],
        headings: List[Dict],
        sections: List[Dict],
    ) -> Dict[str, int | str]:
        return {
            "pages_extracted": len(pages),
            "toc_entries": len(toc),
            "inline_headings": len(headings),
            "sections_built": len(sections),
            "output_dir": str(self.__output_dir),
        }
