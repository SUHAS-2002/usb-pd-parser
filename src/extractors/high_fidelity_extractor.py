"""
High-fidelity PDF extractor (compact OOP, ≤79 chars).

Features:
  - Multi-column text extraction
  - Table/diagram text preservation
  - OCR fallback for non-text blocks
"""

import fitz
import pytesseract
from PIL import Image
from typing import List, Dict

from src.core.extractor_base import BaseExtractor


class HighFidelityExtractor(BaseExtractor):
    """
    Strategy for high-fidelity PDF extraction.

    Public API:
        - extract(pdf_path)

    All implementation details are encapsulated.
    """

    # ------------------------------------------------------------
    # Constructor (private state)
    # ------------------------------------------------------------
    def __init__(self, ocr: bool = True) -> None:
        self.__ocr = self._validate_ocr_flag(ocr)

    # ------------------------------------------------------------
    # Public read-only property
    # ------------------------------------------------------------
    @property
    def ocr(self) -> bool:
        """
        Indicates whether OCR fallback is enabled.
        """
        return self.__ocr

    # ------------------------------------------------------------
    # Template method implementation
    # ------------------------------------------------------------
    def _extract_impl(self, pdf_path: str) -> List[Dict]:
        """
        Extract page text and OCR content from PDF.
        """
        doc = self._open_document(pdf_path)
        output: List[Dict] = []

        for idx, page in enumerate(doc):
            text = self._extract_page_text(page)
            output.append(
                {
                    "page": idx + 1,
                    "text": text,
                }
            )

        return output

    # ------------------------------------------------------------
    # Protected helpers
    # ------------------------------------------------------------
    def _open_document(self, pdf_path: str):
        """
        Open PDF document.
        """
        return fitz.open(pdf_path)

    # ------------------------------------------------------------
    def _extract_page_text(self, page) -> str:
        """
        Extract ordered text blocks from a page.
        """
        blocks = page.get_text("blocks")
        blocks = sorted(blocks, key=lambda b: (b[1], b[0]))

        texts: List[str] = []

        for blk in blocks:
            txt = blk[4].strip()

            if txt:
                texts.append(txt)
                continue

            if self.__ocr:
                ocr_txt = self._extract_ocr_block(page, blk)
                if ocr_txt:
                    texts.append(ocr_txt)

        return "\n".join(texts)

    # ------------------------------------------------------------
    def _extract_ocr_block(self, page, block) -> str:
        """
        Perform OCR on a single non-text block.
        """
        try:
            rect = block[:4]
            pix = page.get_pixmap(clip=rect)
            return self._ocr_pixmap(pix).strip()
        except Exception:
            return ""

    # ------------------------------------------------------------
    def _ocr_pixmap(self, pix) -> str:
        """
        Convert pixmap to text using Tesseract OCR.
        """
        try:
            img = Image.frombytes(
                "RGB",
                [pix.width, pix.height],
                pix.samples,
            )
            return pytesseract.image_to_string(img)
        except Exception:
            return ""

    # ------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------
    def _validate_ocr_flag(self, val: bool) -> bool:
        if not isinstance(val, bool):
            raise ValueError("ocr must be a boolean")
        return val
