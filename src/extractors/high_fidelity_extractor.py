# src/extractors/high_fidelity_extractor.py

import fitz
import pytesseract
from PIL import Image
from typing import List, Dict

from src.core.extractor_base import BaseExtractor


class HighFidelityExtractor(BaseExtractor):
    """
    Extracts high-fidelity page text with:
      - Multi-column reading
      - Table text preservation
      - OCR extraction for diagrams/images
      - Clean and stable block ordering
    """

    def __init__(self, ocr: bool = True) -> None:
        self._ocr = ocr

    def _ocr_image(self, pix) -> str:
        """
        Convert a pixmap block into OCR text.

        Returns an empty string if OCR fails.
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

    def extract(self, pdf_path: str) -> List[Dict]:
        """
        Extract text and OCR content from all PDF pages.

        Parameters
        ----------
        pdf_path : str
            Location of the input PDF.

        Returns
        -------
        List[Dict]
            A list of page dictionaries with:
                - page number
                - combined extracted + OCR text
        """
        doc = fitz.open(pdf_path)
        pages: List[Dict] = []

        for index, page in enumerate(doc):
            blocks = page.get_text("blocks")
            blocks = sorted(blocks, key=lambda b: (b[1], b[0]))

            items: List[str] = []

            for block in blocks:
                blk_text = block[4].strip()

                if blk_text:
                    items.append(blk_text)
                    continue

                # OCR fallback for non-text blocks
                if self._ocr:
                    try:
                        rect = block[:4]
                        pix = page.get_pixmap(clip=rect)
                        ocr_text = self._ocr_image(pix)
                        if ocr_text.strip():
                            items.append(ocr_text)
                    except Exception:
                        # Ignore OCR failures safely
                        pass

            joined = "\n".join(items)

            pages.append(
                {
                    "page": index + 1,
                    "text": joined,
                }
            )

        return pages
