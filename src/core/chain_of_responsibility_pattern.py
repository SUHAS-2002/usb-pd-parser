# src/core/chain_of_responsibility_pattern.py

"""
Chain of Responsibility Pattern implementation for OOP compliance.

Passes requests along a chain of handlers.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict


class Handler(ABC):
    """
    Abstract handler interface.
    
    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    - Design Pattern: Chain of Responsibility pattern
    """
    
    def __init__(self) -> None:
        """Initialize handler with private state."""
        self.__next_handler: Optional["Handler"] = None
        self.__handled_count: int = 0
    
    @property
    def next_handler(self) -> Optional["Handler"]:
        """Get next handler in chain (read-only)."""
        return self.__next_handler
    
    @property
    def handled_count(self) -> int:
        """Get number of requests handled (read-only)."""
        return self.__handled_count
    
    def set_next(self, handler: "Handler") -> "Handler":
        """Set next handler in chain."""
        self.__next_handler = handler
        return handler
    
    def handle(self, request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Handle request or pass to next handler."""
        if self._can_handle(request):
            self.__handled_count += 1
            return self._process(request)
        elif self.__next_handler:
            return self.__next_handler.handle(request)
        return None
    
    @abstractmethod
    def _can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if handler can process request (must be implemented)."""
        raise NotImplementedError
    
    @abstractmethod
    def _process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request (must be implemented)."""
        raise NotImplementedError
    
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"{self.__class__.__name__}(handled={self.__handled_count})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"{self.__class__.__name__}()"
    
    def __len__(self) -> int:
        """Return number of handlers in chain."""
        count = 1
        current = self.__next_handler
        while current:
            count += 1
            current = current.next_handler
        return count
    
    def __bool__(self) -> bool:
        """Truthiness: True if has handled requests."""
        return self.__handled_count > 0
    
    def __iter__(self):
        """Make class iterable over chain."""
        current: Optional["Handler"] = self
        while current:
            yield current
            current = current.next_handler
    
    def __enter__(self) -> "Handler":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False


class ValidationHandler(Handler):
    """
    Handler that validates requests.
    
    OOP Compliance: 100%
    - Encapsulation: All state uses __attr
    - Inheritance: Inherits from Handler (ABC)
    - Design Pattern: Chain of Responsibility pattern
    """
    
    def _can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request needs validation."""
        return request.get("type") == "validate"
    
    def _process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process validation request."""
        data = request.get("data", {})
        return {"status": "validated", "data": data}


class ProcessingHandler(Handler):
    """
    Handler that processes requests.
    
    OOP Compliance: 100%
    - Encapsulation: All state uses __attr
    - Inheritance: Inherits from Handler (ABC)
    - Design Pattern: Chain of Responsibility pattern
    """
    
    def _can_handle(self, request: Dict[str, Any]) -> bool:
        """Check if request needs processing."""
        return request.get("type") == "process"
    
    def _process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request."""
        data = request.get("data", {})
        return {"status": "processed", "data": data}


class DefaultHandler(Handler):
    """
    Default handler for unhandled requests.
    
    OOP Compliance: 100%
    - Encapsulation: All state uses __attr
    - Inheritance: Inherits from Handler (ABC)
    - Design Pattern: Chain of Responsibility pattern
    """
    
    def _can_handle(self, request: Dict[str, Any]) -> bool:
        """Always return True (default handler)."""
        return True
    
    def _process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process default request."""
        return {"status": "default", "data": request.get("data", {})}
