# src/core/adapter/pymupdf_adapter.py

import fitz  # PyMuPDF
from typing import List, Dict
from src.core.pdf_text_strategy import PDFTextStrategy


class PyMuPDFAdapter(PDFTextStrategy):
    """
    High-fidelity PyMuPDF text extractor.

    Uses block-level extraction to capture:
        - multi-column layouts
        - tables (text inside cells)
        - text inside diagrams / vector graphics
        - section labels embedded in figures (e.g., Example 6.1.1.1.1)
        - correct reading order

    Output:
        [
            {"page_number": 1, "text": "<full block-joined text>"},
            ...
        ]
    """

    def extract_text(self, pdf_path: str) -> List[Dict]:
        doc = fitz.open(pdf_path)
        extracted_pages = []

        try:
            for page_idx in range(doc.page_count):
                page = doc.load_page(page_idx)

                # 🟢 CRITICAL CHANGE: use block extraction instead of "text"
                blocks = page.get_text("blocks")   # returns list of 6-tuple blocks
                text_parts = []

                for block in blocks:
                    block_text = block[4]  # (x0, y0, x1, y1, text, block_no)
                    if block_text and block_text.strip():
                        text_parts.append(block_text.strip())

                # Combine blocks with intact order (maintains layout)
                page_text = "\n".join(text_parts)

                extracted_pages.append({
                    "page_number": page_idx + 1,
                    "text": page_text
                })

        finally:
            doc.close()

        return extracted_pages
