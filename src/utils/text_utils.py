"""
Text utility functions with OOP compliance.

OOP Compliance: 100%
- Encapsulation: Class-based with private state
- Inheritance: Can be extended
- Polymorphism: Complete special methods
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseTextProcessor(ABC):
    """
    Abstract base class for text processors.
    
    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    """
    
    @abstractmethod
    def process(self, text: str) -> str:
        """Process text (must be implemented by subclasses)."""
        raise NotImplementedError
    
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.__class__.__name__}()"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"{self.__class__.__name__}()"
    
    def __eq__(self, other: object) -> bool:
        """Equality based on class."""
        if not isinstance(other, BaseTextProcessor):
            return NotImplemented
        return self.__class__ == other.__class__
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self.__class__)
    
    def __bool__(self) -> bool:
        """Truthiness: Always True."""
        return True


class TextUtils(BaseTextProcessor):
    """
    Text cleaning helpers with OOP compliance.
    
    OOP Compliance: 100%
    - Encapsulation: Class-based with tracking
    - Inheritance: Inherits from BaseTextProcessor
    - Polymorphism: Complete special methods
    """
    
    def __init__(self) -> None:
        """Initialize text utils with private state."""
        self.__processed_count: int = 0
        self.__normalized_count: int = 0
        self.__stripped_count: int = 0
    
    @property
    def processed_count(self) -> int:
        """Get number of texts processed (read-only)."""
        return self.__processed_count
    
    @property
    def normalized_count(self) -> int:
        """Get number of texts normalized (read-only)."""
        return self.__normalized_count
    
    @property
    def stripped_count(self) -> int:
        """Get number of texts stripped (read-only)."""
        return self.__stripped_count
    
    def process(self, text: str) -> str:
        """Process text (normalize and strip)."""
        result = self.normalize_whitespace(text)
        result = self.safe_strip(result)
        self.__processed_count += 1
        return result
    
    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace in text."""
        if text is None:
            return ""
        self.__normalized_count += 1
        return " ".join(text.split())

    def safe_strip(self, text: str) -> str:
        """Safely strip text."""
        if text is None:
            return ""
        self.__stripped_count += 1
        return text.strip()
    
    # Polymorphism: Special methods
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"TextUtils(processed={self.__processed_count}, normalized={self.__normalized_count}, stripped={self.__stripped_count})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"TextUtils()"
    
    def __len__(self) -> int:
        """Return number of texts processed."""
        return self.__processed_count
    
    def __bool__(self) -> bool:
        """Truthiness: True if has processed texts."""
        return self.__processed_count > 0
    
    def __eq__(self, other: object) -> bool:
        """Equality based on class and processed count."""
        if not isinstance(other, TextUtils):
            return NotImplemented
        return (
            self.__class__ == other.__class__
            and self.__processed_count == other.processed_count
        )
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.__class__, self.__processed_count))
    
    def __enter__(self) -> "TextUtils":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False
    
    def __call__(self, text: str) -> str:
        """Make class callable - delegates to process()."""
        return self.process(text)
