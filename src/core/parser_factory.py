# src/core/parser_factory.py

from typing import Protocol, Any

from ..parsers.simple_parser import SimpleParser
from ..parsers.advanced_parser import AdvancedParser
from ..parsers.full_pdf_parser import FullPDFParser


class PDFStrategyProtocol(Protocol):
    """
    Protocol for PDF text extraction strategies.
    """

    def extract_text(self, pdf_path: str) -> Any:
        ...


class ParserFactory:
    """
    Factory for creating parser instances.

    Encapsulation rules:
    - create() is the ONLY public method
    - validation and selection logic is private
    """

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def create(
        self,
        parser_type: str,
        pdf_strategy: PDFStrategyProtocol,
    ):
        self.__validate_strategy(pdf_strategy)
        parser_type = self.__normalize_type(parser_type)

        return self.__build_parser(
            parser_type,
            pdf_strategy,
        )

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------
    def __validate_strategy(
        self,
        pdf_strategy: PDFStrategyProtocol,
    ) -> None:
        if pdf_strategy is None:
            raise ValueError(
                "pdf_strategy must be provided "
                "(Dependency Injection required)."
            )

    # ---------------------------------------------------------
    def __normalize_type(self, parser_type: str) -> str:
        if not isinstance(parser_type, str):
            raise ValueError("parser_type must be a string")
        return parser_type.lower()

    # ---------------------------------------------------------
    def __build_parser(
        self,
        parser_type: str,
        pdf_strategy: PDFStrategyProtocol,
    ):
        if parser_type == "simple":
            return SimpleParser(pdf_strategy)

        if parser_type == "advanced":
            return AdvancedParser(pdf_strategy)

        if parser_type == "full":
            return FullPDFParser(pdf_strategy)

        raise ValueError(
            f"Unknown parser type: '{parser_type}'"
        )
