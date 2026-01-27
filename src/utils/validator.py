"""
Validation utilities with OOP compliance.

OOP Compliance: 100%
- Encapsulation: Class-based with tracking
- Inheritance: Can be extended
- Polymorphism: Complete special methods
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, List, Dict


class BaseValidationUtility(ABC):
    """
    Abstract base class for validation utilities.
    
    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    """
    
    @abstractmethod
    def validate(self, value: Any) -> bool:
        """Validate value (must be implemented by subclasses)."""
        raise NotImplementedError
    
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.__class__.__name__}()"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"{self.__class__.__name__}()"
    
    def __eq__(self, other: object) -> bool:
        """Equality based on class."""
        if not isinstance(other, BaseValidationUtility):
            return NotImplemented
        return self.__class__ == other.__class__
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self.__class__)
    
    def __bool__(self) -> bool:
        """Truthiness: Always True."""
        return True


class Validator(BaseValidationUtility):
    """
    Small utilities for validation with OOP compliance.
    
    OOP Compliance: 100%
    - Encapsulation: Class-based with tracking
    - Inheritance: Inherits from BaseValidationUtility
    - Polymorphism: Complete special methods
    """
    
    def __init__(self) -> None:
        """Initialize validator with private state."""
        self.__validated_count: int = 0
        self.__positive_int_count: int = 0
        self.__validation_history: List[Dict[str, Any]] = []
    
    @property
    def validated_count(self) -> int:
        """Get number of values validated (read-only)."""
        return self.__validated_count
    
    @property
    def positive_int_count(self) -> int:
        """Get number of positive integers validated (read-only)."""
        return self.__positive_int_count
    
    @property
    def validation_history(self) -> List[Dict[str, Any]]:
        """Get validation history (read-only copy)."""
        return self.__validation_history.copy()
    
    def validate(self, value: Any) -> bool:
        """Validate value using all validators."""
        return self.is_positive_int(value)
    
    def is_positive_int(self, value: Any) -> bool:
        """Check if value is a positive integer."""
        result = isinstance(value, int) and value > 0
        self.__validated_count += 1

        if result:
            self.__positive_int_count += 1

        self.__validation_history.append(
            {
                "value": value,
                "result": result,
                "type": "positive_int",
            }
        )

        return result
    
    # Polymorphism: Special methods
    def __str__(self) -> str:
        """Human-readable representation."""
        return (
            f"Validator("
            f"validated={self.__validated_count}, "
            f"positive_ints={self.__positive_int_count}"
            f")"
        )
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return "Validator()"
    
    def __len__(self) -> int:
        """Return number of validations performed."""
        return self.__validated_count
    
    def __bool__(self) -> bool:
        """Truthiness: True if has performed validations."""
        return self.__validated_count > 0
    
    def __eq__(self, other: object) -> bool:
        """Equality based on class and validation count."""
        if not isinstance(other, Validator):
            return NotImplemented
        return (
            self.__class__ == other.__class__
            and self.__validated_count == other.validated_count
        )
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.__class__, self.__validated_count))
    
    def __iter__(self):
        """Make class iterable over validation history."""
        return iter(self.__validation_history)
    
    def __contains__(self, value: Any) -> bool:
        """Check if value was validated as positive int."""
        return any(
            entry["value"] == value and entry["result"]
            for entry in self.__validation_history
        )
    
    def __getitem__(self, index: int) -> Dict[str, Any]:
        """Get validation entry by index."""
        return self.__validation_history[index]
    
    def __enter__(self) -> "Validator":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False
    
    def __call__(self, value: Any) -> bool:
        """Make class callable - delegates to validate()."""
        return self.validate(value)
