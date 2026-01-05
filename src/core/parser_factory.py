# src/core/parser_factory.py

from typing import Dict, Type, List

from src.core.base_parser import BaseParser
from src.core.pdf_text_strategy import PDFTextStrategy

from ..parsers.simple_parser import SimpleParser
from ..parsers.advanced_parser import AdvancedParser
from ..parsers.full_pdf_parser import FullPDFParser


class ParserFactory:
    """
    Factory Pattern: creates parser instances using a registry.

    - Parsers are registered once
    - Creation is centralized
    - Strategy is injected (Dependency Injection)
    - Registry is encapsulated (private)
    """

    __registry: Dict[str, Type[BaseParser]] = {}

    # ---------------------------------------------------------
    @classmethod
    def register(
        cls,
        name: str,
        parser_cls: Type[BaseParser],
    ) -> None:
        """Register a parser type."""
        if not issubclass(parser_cls, BaseParser):
            raise TypeError(
                "parser_cls must inherit from BaseParser"
            )

        cls.__registry[name.lower()] = parser_cls

    # ---------------------------------------------------------
    @classmethod
    def create(
        cls,
        parser_type: str,
        strategy: PDFTextStrategy,
        *args,
        **kwargs,
    ) -> BaseParser:
        """
        Create and return a parser instance.
        """
        if strategy is None:
            raise ValueError(
                "ParserFactory.create() requires a PDFTextStrategy instance."
            )

        key = parser_type.lower()
        if key not in cls.__registry:
            raise ValueError(
                f"Unknown parser type: '{parser_type}'. "
                f"Available: {cls.get_available_types()}"
            )

        return cls.__registry[key](strategy, *args, **kwargs)

    # ---------------------------------------------------------
    @classmethod
    def get_available_types(cls) -> List[str]:
        """Return all registered parser types."""
        return list(cls.__registry.keys())

    # ---------------------------------------------------------
    def __str__(self) -> str:
        return f"ParserFactory(types={self.get_available_types()})"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(registry={self.get_available_types()})"
        )


# ------------------------------------------------------------------
# Built-in parser registrations (ONE-TIME)
# ------------------------------------------------------------------
ParserFactory.register("simple", SimpleParser)
ParserFactory.register("advanced", AdvancedParser)
ParserFactory.register("full", FullPDFParser)
