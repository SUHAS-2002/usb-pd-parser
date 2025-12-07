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
from typing import List, Dict, Optional

from src.core.extractor_base import BaseExtractor


class HighFidelityExtractor(BaseExtractor):
    """
    Strategy for high-fidelity PDF extraction.
    """

    def __init__(self, ocr: bool = True) -> None:
        self._ocr = ocr

    # ---------------------------------------------------------------
    # Encapsulated OCR flag
    # ---------------------------------------------------------------
    @property
    def ocr(self) -> bool:
        return self._ocr

    @ocr.setter
    def ocr(self, val: bool) -> None:
        if not isinstance(val, bool):
            raise ValueError("ocr must be True or False")
        self._ocr = val

    # ---------------------------------------------------------------
    # Internal OCR helper
    # ---------------------------------------------------------------
    def _ocr_img(self, pix) -> str:
        """
        OCR a pixmap into text. Returns empty string on failure.
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
    # Main extract method
    # ---------------------------------------------------------------
    def extract(self, pdf: str) -> List[Dict]:
        """
        Extract page text + OCR content.

        Returns:
          List of {"page": int, "text": str}
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

                if self._ocr:
                    try:
                        rect = blk[:4]
                        pix = page.get_pixmap(clip=rect)
                        ocr_txt = self._ocr_img(pix)
                        if ocr_txt.strip():
                            texts.append(ocr_txt)
                    except Exception:
                        pass

            joined = "\n".join(texts)

            out.append(
                {
                    "page": idx + 1,
                    "text": joined,
                }
            )

        return out
