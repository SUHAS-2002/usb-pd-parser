# src/core/adapter/pypdf_adapter.py
from ..pdf_text_strategy import PDFTextStrategy
from PyPDF2 import PdfReader

class PyPDFAdapter(PDFTextStrategy):
    def extract_text(self, pdf_path: str):
        reader = PdfReader(pdf_path)
        pages = [page.extract_text() for page in reader.pages]
        return {"pages": pages}