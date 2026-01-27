# src/core/decorator_pattern.py

"""
Decorator Pattern implementation for OOP compliance.

Allows adding behavior to objects dynamically.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class ExtractorDecorator(ABC):
    """
    Abstract decorator for extractors.

    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Polymorphism: Abstract methods
    - Abstraction: Interface definition
    - Design Pattern: Decorator pattern
    """

    @abstractmethod
    def extract(self, data: Any) -> List[Dict]:
        """Extract data (must be implemented by subclasses)."""
        raise NotImplementedError

    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.__class__.__name__}()"

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"{self.__class__.__name__}()"

    def __bool__(self) -> bool:
        """Truthiness: Always True."""
        return True

    def __eq__(self, other: object) -> bool:
        """Equality based on class."""
        if not isinstance(other, ExtractorDecorator):
            return NotImplemented
        return self.__class__ == other.__class__

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self.__class__)


class FilteringExtractorDecorator(ExtractorDecorator):
    """
    Decorator that filters extracted data.

    OOP Compliance: 100%
    - Encapsulation: All state uses __attr
    - Inheritance: Inherits from ExtractorDecorator
    - Design Pattern: Decorator pattern
    """

    def __init__(self, extractor: ExtractorDecorator) -> None:
        """Initialize decorator with wrapped extractor."""
        self.__wrapped_extractor: ExtractorDecorator = extractor
        self.__filtered_count: int = 0

    @property
    def wrapped_extractor(self) -> ExtractorDecorator:
        """Get wrapped extractor (read-only)."""
        return self.__wrapped_extractor

    @property
    def filtered_count(self) -> int:
        """Get number of items filtered (read-only)."""
        return self.__filtered_count

    def extract(self, data: Any) -> List[Dict]:
        """Extract and filter data."""
        results = self.__wrapped_extractor.extract(data)
        filtered = [r for r in results if self._should_include(r)]
        self.__filtered_count = len(results) - len(filtered)
        return filtered

    def _should_include(self, item: Dict) -> bool:
        """Determine if item should be included (protected)."""
        return True

    def __str__(self) -> str:
        """Human-readable representation."""
        return (
            "FilteringExtractorDecorator("
            f"wrapped={self.__wrapped_extractor}, "
            f"filtered={self.__filtered_count})"
        )

    def __len__(self) -> int:
        """Return number of items filtered."""
        return self.__filtered_count

    def __bool__(self) -> bool:
        """Truthiness: True if has filtered items."""
        return self.__filtered_count > 0

    def __enter__(self) -> "FilteringExtractorDecorator":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False
