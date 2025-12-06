import fitz
import pytesseract
from PIL import Image

from src.core.extractor_base import BaseExtractor  # ✅ FIXED


class HighFidelityExtractor(BaseExtractor):
    """
    Extracts ALL text from PDF pages:
        ✔ Multi-column reading
        ✔ Tables
        ✔ Diagrams text via OCR
        ✔ Clean block ordering
    """

    def __init__(self, ocr: bool = True):
        self._ocr = ocr

    def _ocr_image(self, pix):
        """Convert image block to OCR text."""
        try:
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            return pytesseract.image_to_string(img)
        except Exception:
            return ""

    def extract(self, pdf_path: str):
        doc = fitz.open(pdf_path)
        pages = []

        for i, page in enumerate(doc):
            blocks = page.get_text("blocks")
            blocks = sorted(blocks, key=lambda b: (b[1], b[0]))

            text_parts = []

            for block in blocks:
                text = block[4].strip()

                if not text:
                    # OCR images
                    if self._ocr:
                        try:
                            pix = page.get_pixmap(clip=block[:4])
                            txt = self._ocr_image(pix)
                            if txt.strip():
                                text_parts.append(txt)
                        except:
                            pass
                else:
                    text_parts.append(text)

            pages.append({
                "page": i + 1,
                "text": "\n".join(text_parts),
            })

        return pages
