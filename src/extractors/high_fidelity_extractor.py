"""
High-fidelity PDF extractor (compact OOP, ≤79 chars).

Features:
  - Multi-column text extraction
  - Table/diagram text preservation
  - OCR fallback for non-text blocks
"""

from __future__ import annotations

import fitz
import pytesseract
import logging
from PIL import Image
from typing import List, Dict, Iterable, Any

from src.core.extractor_base import BaseExtractor
from src.core.pdf_text_strategy import PDFTextStrategy

# ------------------------------------------------------------------
# Module-level logger
# ------------------------------------------------------------------
_logger = logging.getLogger(__name__)


class HighFidelityExtractor(PDFTextStrategy, BaseExtractor):
    """
    High-fidelity OCR-based PDF extraction strategy.

    Encapsulation:
    - OCR flag uses name-mangled private attribute (__ocr)
    - OCR and block handling isolated in protected helpers
    """

    # ---------------------------------------------------------------
    # Constructor (TRUE PRIVATE STATE)
    # ---------------------------------------------------------------
    def __init__(self, ocr: bool = True) -> None:
        self.__ocr: bool = self._validate_ocr(ocr)

    # ---------------------------------------------------------------
    # Strategy metadata
    # ---------------------------------------------------------------
    @property
    def strategy_name(self) -> str:
        return "high_fidelity_ocr"

    # ---------------------------------------------------------------
    # Encapsulation: OCR flag
    # ---------------------------------------------------------------
    @property
    def ocr(self) -> bool:
        """Return OCR enabled flag (read-only)."""
        return self.__ocr

    @ocr.setter
    def ocr(self, value: bool) -> None:
        self.__ocr = self._validate_ocr(value)

    # ---------------------------------------------------------------
    # Validation helpers
    # ---------------------------------------------------------------
    @staticmethod
    def _validate_ocr(value: bool) -> bool:
        if not isinstance(value, bool):
            raise TypeError("ocr must be a boolean value")
        return value

    # ---------------------------------------------------------------
    # Strategy implementation
    # ---------------------------------------------------------------
    def extract_text(self, pdf: str) -> List[Dict]:
        """
        Concrete Strategy implementation.

        Extract text from PDF using high-fidelity OCR strategy.
        """
        pages: List[Dict] = []

        with fitz.open(pdf) as doc:
            for index, page in enumerate(doc):
                page_dict = self._extract_page(page, index)
                pages.append(page_dict)

        self._verify_page_coverage(pages)
        return pages

    # ---------------------------------------------------------------
    # Extracted helpers
    # ---------------------------------------------------------------
    def _extract_page(
        self,
        page: fitz.Page,
        page_index: int,
    ) -> Dict:
        """Extract structured text from a single page."""
        text = self._extract_page_text(page, page_index)
        return {
            "page": page_index + 1,
            "text": text,
        }

    def _extract_page_text(
        self,
        page: fitz.Page,
        page_index: int,
    ) -> str:
        """Extract text blocks from a page."""
        blocks = self._get_sorted_blocks(page)
        texts: List[str] = []

        for block in blocks:
            block_text = self._extract_block_text(
                page,
                block,
                page_index,
            )
            if block_text:
                texts.append(block_text)

        return "\n".join(texts)

    def _get_sorted_blocks(
        self,
        page: fitz.Page,
    ) -> List[Iterable[Any]]:
        """Return blocks sorted top-to-bottom, left-to-right."""
        return sorted(
            page.get_text("blocks"),
            key=lambda b: (b[1], b[0]),
        )

    def _extract_block_text(
        self,
        page: fitz.Page,
        block: Iterable[Any],
        page_index: int,
    ) -> str:
        """Extract text from a block with OCR fallback."""
        text = block[4].strip()
        if text:
            return text

        if not self.__ocr:
            return ""

        return self._ocr_block(page, block, page_index)

    # ---------------------------------------------------------------
    # OCR helpers
    # ---------------------------------------------------------------
    def _ocr_block(
        self,
        page: fitz.Page,
        block: Iterable[Any],
        page_index: int,
    ) -> str:
        """Attempt OCR on a page block."""
        try:
            rect = block[:4]
            pix = page.get_pixmap(clip=rect)
            return self._ocr_pixmap(pix).strip()
        except Exception as exc:
            _logger.debug(
                "OCR failed for block at page %d: %s",
                page_index + 1,
                exc,
                exc_info=exc,
            )
            return ""

    def _ocr_pixmap(self, pix: fitz.Pixmap) -> str:
        """Run OCR on a pixmap and return extracted text."""
        try:
            img = Image.frombytes(
                "RGB",
                (pix.width, pix.height),
                pix.samples,
            )
            return pytesseract.image_to_string(img)
        except Exception as exc:
            _logger.debug(
                "OCR pixmap conversion failed: %s",
                exc,
                exc_info=exc,
            )
            return ""

    # ---------------------------------------------------------------
    # Post-processing validation
    # ---------------------------------------------------------------
    def _verify_page_coverage(self, pages: List[Dict]) -> None:
        page_numbers = {
            p["page"] for p in pages if p.get("page")
        }

        if not page_numbers:
            _logger.warning("No pages extracted from PDF")
            return

        min_page = min(page_numbers)
        max_page = max(page_numbers)

        _logger.info(
            "Page extraction: %d unique pages (range: %d-%d)",
            len(page_numbers),
            min_page,
            max_page,
        )

        expected = set(range(min_page, max_page + 1))
        missing = expected - page_numbers

        if missing:
            _logger.warning(
                "Missing pages detected: %d pages",
                len(missing),
            )
            _logger.warning(
                "Sample missing pages: %s",
                sorted(missing)[:10],
            )
