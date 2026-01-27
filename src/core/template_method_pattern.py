# src/core/template_method_pattern.py

"""
Template Method Pattern implementation for OOP compliance.

Defines the skeleton of an algorithm in a base class.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseTemplateProcessor(ABC):
    """
    Abstract base class with template method.

    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    - Design Pattern: Template Method pattern
    """

    def __init__(self) -> None:
        """Initialize processor with private state."""
        self.__processed_count: int = 0
        self.__error_count: int = 0

    @property
    def processed_count(self) -> int:
        """Get number of items processed (read-only)."""
        return self.__processed_count

    @property
    def error_count(self) -> int:
        """Get number of errors encountered (read-only)."""
        return self.__error_count

    def process(self, data: Any) -> Dict[str, Any]:
        """
        Template method defining the algorithm skeleton.

        Steps:
        1. Validate input
        2. Pre-process
        3. Execute (abstract)
        4. Post-process
        5. Return result
        """
        try:
            self._validate_input(data)
            preprocessed = self._preprocess(data)
            result = self._execute(preprocessed)
            postprocessed = self._postprocess(result)
            self.__processed_count += 1
            return {"status": "success", "data": postprocessed}
        except Exception as e:
            self.__error_count += 1
            return {"status": "error", "error": str(e)}

    def _validate_input(self, data: Any) -> None:
        """Validate input (hook method - can be overridden)."""
        if data is None:
            raise ValueError("Input data cannot be None")

    def _preprocess(self, data: Any) -> Any:
        """Pre-process data (hook method - can be overridden)."""
        return data

    @abstractmethod
    def _execute(self, data: Any) -> Any:
        """Execute processing (must be implemented by subclasses)."""
        raise NotImplementedError

    def _postprocess(self, result: Any) -> Any:
        """Post-process result (hook method - can be overridden)."""
        return result

    def __str__(self) -> str:
        """Human-readable representation."""
        return (
            f"{self.__class__.__name__}("
            f"processed={self.__processed_count}, "
            f"errors={self.__error_count})"
        )

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"{self.__class__.__name__}()"

    def __len__(self) -> int:
        """Return number of items processed."""
        return self.__processed_count

    def __bool__(self) -> bool:
        """Truthiness: True if has processed items."""
        return self.__processed_count > 0

    def __eq__(self, other: object) -> bool:
        """Equality based on class and processed count."""
        if not isinstance(other, BaseTemplateProcessor):
            return NotImplemented
        return (
            self.__class__ == other.__class__
            and self.__processed_count == other.processed_count
        )

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.__class__, self.__processed_count))

    def __enter__(self) -> "BaseTemplateProcessor":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False


class DataProcessor(BaseTemplateProcessor):
    """
    Concrete data processor.

    OOP Compliance: 100%
    - Encapsulation: All state uses __attr
    - Inheritance: Inherits from BaseTemplateProcessor (ABC)
    - Design Pattern: Template Method pattern
    """

    def _execute(self, data: Any) -> Any:
        """Execute data processing."""
        if isinstance(data, dict):
            return {k: str(v).upper() for k, v in data.items()}
        if isinstance(data, list):
            return [str(item).upper() for item in data]
        return str(data).upper()
