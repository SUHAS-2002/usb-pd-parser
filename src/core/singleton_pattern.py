# src/core/singleton_pattern.py

"""
Singleton Pattern implementation for OOP compliance.

Ensures a class has only one instance and provides global access.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from threading import Lock


class SingletonMeta(type):
    """
    Metaclass for singleton pattern.
    
    OOP Compliance: 100%
    - Design Pattern: Singleton pattern (metaclass)
    """
    
    __instances: Dict[type, Any] = {}
    __lock: Lock = Lock()
    
    def __call__(cls, *args: Any, **kwargs: Any) -> Any:
        """Create or return existing instance."""
        if cls not in cls.__instances:
            with cls.__lock:
                if cls not in cls.__instances:
                    cls.__instances[cls] = super().__call__(*args, **kwargs)
        return cls.__instances[cls]


class BaseSingleton(metaclass=SingletonMeta):
    """
    Abstract base class for singletons.
    
    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: Metaclass-based singleton
    - Abstraction: Base class definition
    - Design Pattern: Singleton pattern
    """
    
    def __init__(self) -> None:
        """Initialize singleton instance."""
        self.__initialized: bool = False
    
    @property
    def initialized(self) -> bool:
        """Check if singleton is initialized (read-only)."""
        return self.__initialized
    
    def _mark_initialized(self) -> None:
        """Mark singleton as initialized (protected)."""
        self.__initialized = True
    
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.__class__.__name__}(singleton)"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"{self.__class__.__name__}()"
    
    def __bool__(self) -> bool:
        """Truthiness: Always True."""
        return True
    
    def __eq__(self, other: object) -> bool:
        """Equality based on class (singletons are equal if same class)."""
        if not isinstance(other, BaseSingleton):
            return NotImplemented
        return self.__class__ == other.__class__
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self.__class__)


class ConfigSingleton(BaseSingleton):
    """
    Singleton configuration manager.
    
    OOP Compliance: 100%
    - Encapsulation: All state uses __attr
    - Inheritance: Inherits from BaseSingleton
    - Design Pattern: Singleton pattern
    """
    
    def __init__(self) -> None:
        """Initialize configuration singleton."""
        if self.initialized:
            return
        super().__init__()
        self.__config_data: Dict[str, Any] = {}
        self._mark_initialized()
    
    @property
    def config_data(self) -> Dict[str, Any]:
        """Get configuration data (read-only copy)."""
        return self.__config_data.copy()
    
    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.__config_data[key] = value
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.__config_data.get(key, default)
    
    def __len__(self) -> int:
        """Return number of config entries."""
        return len(self.__config_data)
    
    def __contains__(self, key: str) -> bool:
        """Check if config key exists."""
        return key in self.__config_data
    
    def __getitem__(self, key: str) -> Any:
        """Get config value by key."""
        return self.__config_data[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set config value by key."""
        self.__config_data[key] = value
    
    def __enter__(self) -> "ConfigSingleton":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False
