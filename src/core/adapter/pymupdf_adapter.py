# src/core/adapter/pymupdf_adapter.py
import fitz  # PyMuPDF
from ..pdf_text_strategy import PDFTextStrategy
from typing import List, Dict

class PyMuPDFAdapter(PDFTextStrategy):
    """
    PyMuPDF adapter returns a list of dicts:
    [{"page_number": 1, "text": "..." }, ...]
    """
    def extract_text(self, pdf_path: str) -> List[Dict]:
        doc = fitz.open(pdf_path)
        pages = []
        try:
            for page_number in range(doc.page_count):
                page = doc.load_page(page_number)
                text = page.get_text("text")  # plain text
                pages.append({"page_number": page_number + 1, "text": text})
        finally:
            doc.close()
        return pages
