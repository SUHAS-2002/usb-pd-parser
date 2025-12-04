from ..pdf_text_strategy import PDFTextStrategy
import pdfminer.high_level

class PDFMinerAdapter(PDFTextStrategy):
    def extract_text(self, pdf_path: str):
        with open(pdf_path, "rb") as f:
            text = pdfminer.high_level.extract_text(f)
        return {"pages": text.split("\f")}
