# src/core/parser_factory.py

from typing import Protocol
from ..parsers.simple_parser import SimpleParser
from ..parsers.advanced_parser import AdvancedParser
from ..parsers.full_pdf_parser import FullPDFParser


class PDFStrategyProtocol(Protocol):
    """
    Protocol for PDF text extraction strategies.
    Any strategy must implement extract_text().
    """

    def extract_text(self, pdf_path: str):
        ...


class ParserFactory:
    """
    Factory Pattern: creates parser instances based on `parser_type`.

    The factory does NOT create PDF text extraction strategies.
    A strategy instance must be supplied from outside
    (Dependency Injection → clean OOP, SOLID-compliant).
    """

    @staticmethod
    def create(
        parser_type: str = "advanced",
        pdf_strategy: PDFStrategyProtocol = None
    ):
        """
        Create and return a parser instance.

        Parameters
        ----------
        parser_type : str
            One of: "simple", "advanced", "full".
        pdf_strategy : object
            A PDF text extraction strategy implementing extract_text().

        Returns
        -------
        object
            Instance of SimpleParser, AdvancedParser, or FullPDFParser.

        Raises
        ------
        ValueError
            If pdf_strategy is missing or parser_type is unknown.
        """
        if pdf_strategy is None:
            raise ValueError(
                "ParserFactory.create() requires a pdf_strategy instance. "
                "Inject the strategy externally to follow good OOP design."
            )

        parser_type = parser_type.lower()

        if parser_type == "simple":
            return SimpleParser(pdf_strategy)

        if parser_type == "advanced":
            return AdvancedParser(pdf_strategy)

        if parser_type == "full":
            return FullPDFParser(pdf_strategy)

        raise ValueError(f"Unknown parser type: '{parser_type}'")
