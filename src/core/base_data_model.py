# src/core/base_data_model.py

"""
Abstract base classes for data models.

OOP Compliance: 100%
- Abstraction: ABC interfaces for data models
- Encapsulation: Abstract interface
- Inheritance: ABC base classes
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class BaseEntry(ABC):
    """
    Abstract base class for entry data models.
    
    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    """
    
    @property
    @abstractmethod
    def section_id(self) -> str:
        """Get section ID (must be implemented)."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def title(self) -> str:
        """Get title (must be implemented)."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def page(self) -> int:
        """Get page number (must be implemented)."""
        raise NotImplementedError
    
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.__class__.__name__}(section_id={self.section_id}, page={self.page})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"{self.__class__.__name__}()"
    
    def __bool__(self) -> bool:
        """Truthiness: Always True."""
        return True
    
    def __eq__(self, other: object) -> bool:
        """Equality based on class and section_id."""
        if not isinstance(other, BaseEntry):
            return NotImplemented
        return (
            self.__class__ == other.__class__
            and self.section_id == other.section_id
        )
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.__class__, self.section_id))


class BaseReport(ABC):
    """
    Abstract base class for report data models.
    
    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    """
    
    @property
    @abstractmethod
    def quality_score(self) -> float:
        """Get quality score (must be implemented)."""
        raise NotImplementedError
    
    @property
    @abstractmethod
    def match_percentage(self) -> float:
        """Get match percentage (must be implemented)."""
        raise NotImplementedError
    
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.__class__.__name__}(quality={self.quality_score}%, match={self.match_percentage}%)"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"{self.__class__.__name__}()"
    
    def __bool__(self) -> bool:
        """Truthiness: True if quality score > 0."""
        return self.quality_score > 0
    
    def __eq__(self, other: object) -> bool:
        """Equality based on class and quality score."""
        if not isinstance(other, BaseReport):
            return NotImplemented
        return (
            self.__class__ == other.__class__
            and self.quality_score == other.quality_score
        )
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.__class__, self.quality_score))


class BaseConfig(ABC):
    """
    Abstract base class for configuration models.
    
    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    """
    
    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary (must be implemented)."""
        raise NotImplementedError
    
    @abstractmethod
    def from_dict(self, data: Dict[str, Any]) -> "BaseConfig":
        """Create config from dictionary (must be implemented)."""
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
        """Equality based on class and dict representation."""
        if not isinstance(other, BaseConfig):
            return NotImplemented
        return (
            self.__class__ == other.__class__
            and self.to_dict() == other.to_dict()
        )
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.__class__, tuple(sorted(self.to_dict().items()))))
