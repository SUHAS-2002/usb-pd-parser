from ..core.base_parser import BaseParser
from ..core.pdf_text_strategy import PDFTextStrategy

class SimpleParser(BaseParser):
    def __init__(self, strategy: PDFTextStrategy):
        super().__init__(strategy)


class SimpleParser(BaseParser):
    def __init__(self, strategy: PDFTextStrategy):
        self.pdf_strategy = strategy

    def parse(self):
        # Implement your simple parsing logic here
        pdf_data = self.pdf_strategy.extract_text(self.pdf_path)
        return pdf_data
