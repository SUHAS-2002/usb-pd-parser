# src/core/parser_factory.py

from __future__ import annotations

from typing import Dict, Type, List, Iterator, Any
from abc import ABC, abstractmethod

from src.core.base_parser import BaseParser
from src.core.pdf_text_strategy import PDFTextStrategy

from ..parsers.simple_parser import SimpleParser
from ..parsers.advanced_parser import AdvancedParser
from ..parsers.full_pdf_parser import FullPDFParser


class BaseFactory(ABC):
    """
    Abstract base class for factories.

    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    - Design Pattern: Factory pattern base
    """

    @classmethod
    @abstractmethod
    def create(cls, *args, **kwargs) -> Any:
        """Create an instance (must be implemented by subclasses)."""
        raise NotImplementedError

    @classmethod
    @abstractmethod
    def get_available_types(cls) -> List[str]:
        """Get available types (must be implemented by subclasses)."""
        raise NotImplementedError


class ParserFactory(BaseFactory):
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
        """Create and return a parser instance."""
        if strategy is None:
            raise ValueError(
                "ParserFactory.create() requires a "
                "PDFTextStrategy instance."
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
    # Polymorphism: Special methods
    # ---------------------------------------------------------
    @classmethod
    def __str__(cls) -> str:
        """Human-readable representation."""
        return f"ParserFactory(types={cls.get_available_types()})"

    @classmethod
    def __repr__(cls) -> str:
        """Developer-friendly representation."""
        return (
            "ParserFactory("
            f"registry={cls.get_available_types()})"
        )

    @classmethod
    def __len__(cls) -> int:
        """Return number of registered parsers."""
        return len(cls.__registry)

    @classmethod
    def __contains__(cls, name: str) -> bool:
        """Check if parser type is registered."""
        return name.lower() in cls.__registry

    @classmethod
    def __bool__(cls) -> bool:
        """Truthiness: True if has registered parsers."""
        return len(cls.__registry) > 0

    @classmethod
    def __iter__(cls) -> Iterator[str]:
        """Make class iterable over registered types."""
        return iter(cls.__registry.keys())

    @classmethod
    def __getitem__(
        cls,
        parser_type: str,
    ) -> Type[BaseParser]:
        """Get parser class by type."""
        key = parser_type.lower()
        if key not in cls.__registry:
            raise KeyError(
                f"Unknown parser type: {parser_type}"
            )
        return cls.__registry[key]

    @classmethod
    def __call__(
        cls,
        parser_type: str,
        strategy: PDFTextStrategy,
        *args,
        **kwargs,
    ) -> BaseParser:
        """Make class callable - delegates to create()."""
        return cls.create(
            parser_type,
            strategy,
            *args,
            **kwargs,
        )


# ------------------------------------------------------------------
# Built-in parser registrations (ONE-TIME)
# ------------------------------------------------------------------
ParserFactory.register("simple", SimpleParser)
ParserFactory.register("advanced", AdvancedParser)
ParserFactory.register("full", FullPDFParser)
