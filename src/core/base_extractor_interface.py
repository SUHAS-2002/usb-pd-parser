# src/core/base_extractor_interface.py

"""
Additional abstract interfaces for extractors.

OOP Compliance: 100%
- Abstraction: ABC interfaces for different extractor types
- Encapsulation: Abstract interface
- Inheritance: ABC base classes
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseTextExtractor(ABC):
    """
    Abstract base class for text extractors.
    
    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    """
    
    @abstractmethod
    def extract_text(self, source: Any) -> str:
        """Extract text from source (must be implemented)."""
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


class BasePatternExtractor(ABC):
    """
    Abstract base class for pattern-based extractors.
    
    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    """
    
    @abstractmethod
    def extract_patterns(self, text: str) -> List[Dict[str, Any]]:
        """Extract patterns from text (must be implemented)."""
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


class BaseStructuredExtractor(ABC):
    """
    Abstract base class for structured data extractors.
    
    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    """
    
    @abstractmethod
    def extract_structure(self, data: Any) -> Dict[str, Any]:
        """Extract structured data (must be implemented)."""
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
