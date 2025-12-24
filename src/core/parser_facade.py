# src/core/parser_facade.py

from typing import Dict, Any

from .parser_factory import ParserFactory
from .adapter.pymupdf_adapter import PyMuPDFAdapter
from ..extractors.toc_extractor import ToCExtractor
from ..extractors.chunk_extractor import ChunkExtractor
from ..extractors.table_extractor import TableExtractor


class ParserFacade:
    """
    Facade that composes parser, PDF extraction strategy,
    and extractor components.

    Encapsulation rules:
    - parse_pdf() is the ONLY public method
    - all collaborators are private
    - pipeline stages are isolated
    """

    # ---------------------------------------------------------
    # Construction (private composition)
    # ---------------------------------------------------------
    def __init__(self, parser_type: str = "advanced") -> None:
        self.__strategy = self.__create_strategy()
        self.__parser = self.__create_parser(
            parser_type,
            self.__strategy,
        )

        self.__toc_extractor = ToCExtractor()
        self.__chunk_extractor = ChunkExtractor()
        self.__table_extractor = TableExtractor()

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def parse_pdf(self, pdf_path: str) -> Dict[str, Any]:
        self.__configure_parser(pdf_path)

        pdf_data = self.__parse_pdf()
        toc = self.__extract_toc(pdf_data)
        chunks = self.__extract_chunks(pdf_data)
        tables = self.__extract_tables(pdf_data)

        return {
            "toc": toc,
            "chunks": chunks,
            "tables": tables,
            "sections": pdf_data,
        }

    # ---------------------------------------------------------
    # Private helpers (construction)
    # ---------------------------------------------------------
    def __create_strategy(self):
        return PyMuPDFAdapter()

    # ---------------------------------------------------------
    def __create_parser(self, parser_type: str, strategy):
        return ParserFactory.create(
            parser_type=parser_type,
            pdf_strategy=strategy,
        )

    # ---------------------------------------------------------
    # Private helpers (pipeline)
    # ---------------------------------------------------------
    def __configure_parser(self, pdf_path: str) -> None:
        self.__parser.pdf_path = pdf_path

    # ---------------------------------------------------------
    def __parse_pdf(self):
        return self.__parser.parse()

    # ---------------------------------------------------------
    def __extract_toc(self, pdf_data):
        return self.__toc_extractor.extract(pdf_data)

    # ---------------------------------------------------------
    def __extract_chunks(self, pdf_data):
        return self.__chunk_extractor.extract(pdf_data)

    # ---------------------------------------------------------
    def __extract_tables(self, pdf_data):
        return self.__table_extractor.extract(pdf_data)
