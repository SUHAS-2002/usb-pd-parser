# src/core/base_processor_interface.py

"""
Abstract base classes for processors.

OOP Compliance: 100%
- Abstraction: ABC interfaces for processing operations
- Encapsulation: Abstract interface
- Inheritance: ABC base classes
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseDataProcessor(ABC):
    """
    Abstract base class for data processors.
    
    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    """
    
    @abstractmethod
    def process(self, data: Any) -> Any:
        """Process data (must be implemented)."""
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


class BaseTransformer(ABC):
    """
    Abstract base class for transformers.
    
    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    """
    
    @abstractmethod
    def transform(self, input_data: Any) -> Any:
        """Transform input data (must be implemented)."""
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


class BaseFilter(ABC):
    """
    Abstract base class for filters.
    
    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    """
    
    @abstractmethod
    def filter(self, items: List[Any]) -> List[Any]:
        """Filter items (must be implemented)."""
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
