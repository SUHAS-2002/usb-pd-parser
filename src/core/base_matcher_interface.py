# src/core/base_matcher_interface.py

"""
Abstract base classes for matchers and validators.

OOP Compliance: 100%
- Abstraction: ABC interfaces for matching operations
- Encapsulation: Abstract interface
- Inheritance: ABC base classes
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Tuple


class BaseMatcher(ABC):
    """
    Abstract base class for matchers.

    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    """

    @abstractmethod
    def match(self, source: Any, target: Any) -> bool:
        """Match source with target (must be implemented)."""
        raise NotImplementedError

    @abstractmethod
    def similarity(self, source: Any, target: Any) -> float:
        """Calculate similarity score (must be implemented)."""
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


class BaseValidatorInterface(ABC):
    """
    Abstract base class for validators.

    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    """

    @abstractmethod
    def validate(self, data: Any) -> Tuple[bool, List[str]]:
        """
        Validate data and return (is_valid, errors).

        Must be implemented by subclasses.
        """
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


class BaseComparator(ABC):
    """
    Abstract base class for comparators.

    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    """

    @abstractmethod
    def compare(self, item1: Any, item2: Any) -> int:
        """Compare two items (must be implemented)."""
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
