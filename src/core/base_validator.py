# src/core/base_validator.py

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, List


class BaseValidator(ABC):
    """
    Abstract base class for all validators.
    
    Provides common validation functionality.
    All internal state uses name mangling (__attr) for true privacy.
    """

    def __init__(self) -> None:
        """Initialize validator with private state."""
        self.__validated_count: int = 0
        self.__error_count: int = 0
        self.__warnings: List[str] = []
    
    # Encapsulation: Properties (read-only)
    @property
    def validated_count(self) -> int:
        """Get number of items validated (read-only)."""
        return self.__validated_count
    
    @property
    def error_count(self) -> int:
        """Get number of validation errors (read-only)."""
        return self.__error_count
    
    @property
    def warnings(self) -> List[str]:
        """Get validation warnings (read-only copy)."""
        return self.__warnings.copy()
    
    # Abstract method (must be implemented by subclasses)
    @abstractmethod
    def validate(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        """Perform validation (must be implemented by subclasses)."""
        raise NotImplementedError
    
    # Protected methods for subclasses
    def _increment_validated(self) -> None:
        """Increment validated counter (protected)."""
        self.__validated_count += 1
    
    def _add_warning(self, warning: str) -> None:
        """Add validation warning (protected)."""
        self.__warnings.append(warning)
    
    def _increment_errors(self) -> None:
        """Increment error counter (protected)."""
        self.__error_count += 1
    
    # Polymorphism: Special methods
    def __str__(self) -> str:
        """Human-readable representation."""
        return (
            f"{self.__class__.__name__}("
            f"validated={self.__validated_count}, "
            f"errors={self.__error_count}, "
            f"warnings={len(self.__warnings)})"
        )
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"{self.__class__.__name__}()"
    
    def __len__(self) -> int:
        """Return number of items validated."""
        return self.__validated_count
    
    def __bool__(self) -> bool:
        """Truthiness: True if has validated items."""
        return self.__validated_count > 0
    
    def __eq__(self, other: object) -> bool:
        """Equality based on class and validation count."""
        if not isinstance(other, BaseValidator):
            return NotImplemented
        return (
            self.__class__ == other.__class__
            and self.__validated_count == other.__validated_count
        )
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.__class__, self.__validated_count))
    
    def __enter__(self) -> "BaseValidator":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False
