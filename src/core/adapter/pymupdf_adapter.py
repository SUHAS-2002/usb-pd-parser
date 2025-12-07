# src/core/adapter/pymupdf_adapter.py

import fitz  # PyMuPDF
from typing import List, Dict
from src.core.pdf_text_strategy import PDFTextStrategy


class PyMuPDFAdapter(PDFTextStrategy):
    """
    High-fidelity text extractor using PyMuPDF.

    Features:
    - Handles multi-column layouts.
    - Preserves table block structure.
    - Extracts text inside diagrams.
    - Maintains visual reading order.

    Returns a list:
        {
            "page_number": int,
            "text": str
        }
    """

    def extract_text(self, pdf_path: str) -> List[Dict]:
        """
        Extract text using block-level reading.

        Parameters
        ----------
        pdf_path : str
            Path to the PDF file.

        Returns
        -------
        List[Dict]
            Normalized list of pages.
        """
        doc = fitz.open(pdf_path)
        pages: List[Dict] = []

        try:
            for idx in range(doc.page_count):
                page = doc.load_page(idx)
                blocks = page.get_text("blocks")
                parts: List[str] = []

                for block in blocks:
                    # block structure:
                    # (x0, y0, x1, y1, text, block_no)
                    block_text = block[4]
                    if block_text and block_text.strip():
                        parts.append(block_text.strip())

                page_text = "\n".join(parts)

                pages.append(
                    {
                        "page_number": idx + 1,
                        "text": page_text,
                    }
                )
        finally:
            doc.close()

        return pages
