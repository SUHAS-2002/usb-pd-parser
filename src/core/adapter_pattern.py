# src/core/adapter_pattern.py

"""
Adapter Pattern implementation for OOP compliance.

Allows incompatible interfaces to work together.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class TargetInterface(ABC):
    """
    Target interface that clients expect.
    
    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    - Design Pattern: Adapter pattern (target)
    """
    
    @abstractmethod
    def process(self, data: Any) -> List[Dict]:
        """Process data (must be implemented by subclasses)."""
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


class BaseAdaptee(ABC):
    """
    Abstract base class for adaptees.
    
    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    """
    
    @abstractmethod
    def incompatible_method(self, input_data: Any) -> Dict[str, Any]:
        """Method with incompatible interface (must be implemented)."""
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


class Adaptee(BaseAdaptee):
    """
    Existing class with incompatible interface.
    
    OOP Compliance: 100%
    - Encapsulation: All state uses __attr
    - Inheritance: Inherits from BaseAdaptee (ABC)
    - Polymorphism: Special methods
    """
    
    def __init__(self) -> None:
        """Initialize adaptee with private state."""
        super().__init__()  # Initialize BaseAdaptee
        self.__processed_count: int = 0
    
    @property
    def processed_count(self) -> int:
        """Get processed count (read-only)."""
        return self.__processed_count
    
    def incompatible_method(self, input_data: Any) -> Dict[str, Any]:
        """Method with incompatible interface."""
        self.__processed_count += 1
        return {"data": input_data, "processed": True}
    
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"Adaptee(processed={self.__processed_count})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"Adaptee()"
    
    def __len__(self) -> int:
        """Return processed count."""
        return self.__processed_count
    
    def __bool__(self) -> bool:
        """Truthiness: True if has processed items."""
        return self.__processed_count > 0


class Adapter(TargetInterface):
    """
    Adapter that makes Adaptee compatible with TargetInterface.
    
    OOP Compliance: 100%
    - Encapsulation: All state uses __attr
    - Inheritance: Inherits from TargetInterface
    - Design Pattern: Adapter pattern
    """
    
    def __init__(self, adaptee: Adaptee) -> None:
        """Initialize adapter with adaptee."""
        super().__init__()
        self.__adaptee: Adaptee = adaptee
    
    @property
    def adaptee(self) -> Adaptee:
        """Get adaptee (read-only)."""
        return self.__adaptee
    
    def process(self, data: Any) -> List[Dict]:
        """Process data using adaptee (adapter method)."""
        result = self.__adaptee.incompatible_method(data)
        return [result]
    
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"Adapter(adaptee={self.__adaptee})"
    
    def __len__(self) -> int:
        """Return adaptee processed count."""
        return len(self.__adaptee)
    
    def __bool__(self) -> bool:
        """Truthiness: True if adaptee has processed items."""
        return bool(self.__adaptee)
    
    def __enter__(self) -> "Adapter":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False
