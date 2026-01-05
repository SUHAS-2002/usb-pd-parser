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
from src.core.pdf_text_strategy import PDFTextStrategy


class HighFidelityExtractor(PDFTextStrategy, BaseExtractor):
    """
    High-fidelity OCR-based PDF extraction strategy.
    """

    # ---------------------------------------------------------------
    def __init__(self, ocr: bool = True) -> None:
        self.__ocr: bool = self._validate_ocr(ocr)

    # ---------------------------------------------------------------
    # Strategy metadata
    # ---------------------------------------------------------------
    @property
    def strategy_name(self) -> str:
        """Return the name of this extraction strategy."""
        return "high_fidelity_ocr"

    # ---------------------------------------------------------------
    # Encapsulation: OCR flag
    # ---------------------------------------------------------------
    @property
    def ocr(self) -> bool:
        """Return whether OCR fallback is enabled."""
        return self.__ocr

    @ocr.setter
    def ocr(self, value: bool) -> None:
        """Enable or disable OCR fallback."""
        self.__ocr = self._validate_ocr(value)

    # ---------------------------------------------------------------
    # Validation helpers
    # ---------------------------------------------------------------
    def _validate_ocr(self, value: bool) -> bool:
        if not isinstance(value, bool):
            raise ValueError("ocr must be a boolean value")
        return value

    # ---------------------------------------------------------------
    # Internal OCR helper
    # ---------------------------------------------------------------
    def _ocr_img(self, pix) -> str:
        """
        OCR a pixmap into text.
        Returns empty string on failure.
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

    # ---------------------------------------------------------------
    # Strategy implementation
    # ---------------------------------------------------------------
    def extract_text(self, pdf: str) -> List[Dict]:
        """
        Concrete Strategy implementation.

        NOTE:
        This method contains the SAME logic that previously
        existed in extract(). Behavior is unchanged.
        """
        doc = fitz.open(pdf)
        out: List[Dict] = []

        for idx, page in enumerate(doc):
            blocks = page.get_text("blocks")
            blocks = sorted(
                blocks,
                key=lambda b: (b[1], b[0]),
            )

            texts: List[str] = []

            for blk in blocks:
                txt = blk[4].strip()

                if txt:
                    texts.append(txt)
                    continue

                if self.__ocr:
                    try:
                        rect = blk[:4]
                        pix = page.get_pixmap(clip=rect)
                        ocr_txt = self._ocr_img(pix)
                        if ocr_txt.strip():
                            texts.append(ocr_txt)
                    except Exception:
                        pass

            out.append(
                {
                    "page": idx + 1,
                    "text": "\n".join(texts),
                }
            )

        return out
