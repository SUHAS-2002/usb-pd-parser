# src/core/extractor_base.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseExtractor(ABC):
    """
    Abstract base class for all extractors with maximum encapsulation.
    
    Provides common functionality and enforces interface.
    All internal state uses name mangling (__attr) for true privacy.
    """

    def __init__(self) -> None:
        """Initialize extractor with private state."""
        self.__extracted_count: int = 0
        self.__error_count: int = 0
        self.__last_error: str | None = None
    
    # Encapsulation: Properties (read-only)
    @property
    def extracted_count(self) -> int:
        """Get number of items extracted (read-only)."""
        return self.__extracted_count
    
    @property
    def error_count(self) -> int:
        """Get number of errors encountered (read-only)."""
        return self.__error_count
    
    @property
    def last_error(self) -> str | None:
        """Get last error message (read-only)."""
        return self.__last_error
    
    # Abstract method (must be implemented by subclasses)
    @abstractmethod
    def extract(self, data: Any) -> List[Dict]:
        """
        Extract data (must be implemented by subclasses).
        
        Parameters
        ----------
        data : Any
            Input data to extract from.
        
        Returns
        -------
        List[Dict]
            A list where each entry contains extracted data.
        """
        raise NotImplementedError
    
    # Protected methods for subclasses
    def _increment_count(self) -> None:
        """Increment extraction counter (protected)."""
        self.__extracted_count += 1
    
    def _record_error(self, error: str) -> None:
        """Record error (protected)."""
        self.__error_count += 1
        self.__last_error = error
    
    # Polymorphism: Special methods
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.__class__.__name__}(count={self.__extracted_count}, errors={self.__error_count})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"{self.__class__.__name__}()"
    
    def __len__(self) -> int:
        """Return number of items extracted."""
        return self.__extracted_count
    
    def __bool__(self) -> bool:
        """Truthiness: True if has extracted items."""
        return self.__extracted_count > 0
    
    def __eq__(self, other: object) -> bool:
        """Equality based on class and extraction count."""
        if not isinstance(other, BaseExtractor):
            return NotImplemented
        return (
            self.__class__ == other.__class__
            and self.__extracted_count == other.extracted_count
        )
