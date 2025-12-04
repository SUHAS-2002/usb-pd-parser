from .adapter.pdfminer_adapter import PDFMinerAdapter
from .adapter.pymupdf_adapter import PyMuPDFAdapter
from .adapter.pypdf_adapter import PyPDFAdapter

from ..parsers.simple_parser import SimpleParser
from ..parsers.advanced_parser import AdvancedParser
from ..parsers.full_pdf_parser import FullPDFParser

class ParserFactory:
    """Factory to create parser instances with a PDF text strategy."""

    @staticmethod
    def create(parser_type="advanced", pdf_strategy=None):
        if pdf_strategy is None:
            pdf_strategy = PDFMinerAdapter()

        parser_type = parser_type.lower()
        if parser_type == "simple":
            return SimpleParser(pdf_strategy)
        elif parser_type == "advanced":
            return AdvancedParser(pdf_strategy)
        elif parser_type == "full":
            return FullPDFParser(pdf_strategy)
        else:
            raise ValueError(f"Unknown parser type: {parser_type}")
