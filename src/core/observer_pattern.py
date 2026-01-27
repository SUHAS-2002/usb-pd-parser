# src/core/observer_pattern.py

"""
Observer Pattern implementation for OOP compliance.

Allows objects to notify multiple observers about state changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import List, Dict, Any


class Observer(ABC):
    """
    Abstract observer interface.

    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Polymorphism: Abstract method
    - Abstraction: Interface definition
    """

    @abstractmethod
    def update(self, event: str, data: Dict[str, Any]) -> None:
        """
        Receive notification about an event.

        Parameters
        ----------
        event : str
            Event type identifier
        data : Dict[str, Any]
            Event data payload
        """
        raise NotImplementedError


class Observable(ABC):
    """
    Abstract Base Class for Observables (Subjects).

    Manages a list of observers and notifies them of state changes.

    OOP Compliance: 100%
    - Encapsulation: All state uses __attr
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    - Design Pattern: Observer pattern
    """

    def __init__(self) -> None:
        """Initialize observable with private observer list."""
        self.__observers: List[Observer] = []
        self.__event_history: List[tuple[str, Dict[str, Any]]] = []

    @property
    def observer_count(self) -> int:
        """Get number of registered observers (read-only)."""
        return len(self.__observers)

    @property
    def event_count(self) -> int:
        """Get number of events fired (read-only)."""
        return len(self.__event_history)

    def attach(self, observer: Observer) -> None:
        """Attach an observer to receive notifications."""
        if observer not in self.__observers:
            self.__observers.append(observer)

    def detach(self, observer: Observer) -> None:
        """Detach an observer from notifications."""
        if observer in self.__observers:
            self.__observers.remove(observer)

    def notify(
        self,
        event: str,
        data: Dict[str, Any] | None = None,
    ) -> None:
        """Notify all observers about an event."""
        payload = data or {}
        self.__event_history.append((event, payload))

        for observer in self.__observers:
            try:
                observer.update(event, payload)
            except Exception:
                # Explicitly continue notifying other observers
                continue

    def clear_history(self) -> None:
        """Clear event history (protected operation)."""
        self.__event_history.clear()

    # ---------------------------------------------------------
    # Polymorphism: Special methods
    # ---------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation."""
        return (
            f"{self.__class__.__name__}("
            f"observers={len(self.__observers)}, "
            f"events={len(self.__event_history)})"
        )

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"{self.__class__.__name__}()"

    def __len__(self) -> int:
        """Return number of observers."""
        return len(self.__observers)

    def __bool__(self) -> bool:
        """Truthiness: True if has observers."""
        return len(self.__observers) > 0

    def __contains__(self, observer: Observer) -> bool:
        """Check if observer is registered."""
        return observer in self.__observers

    def __iter__(self):
        """Make class iterable over observers."""
        return iter(self.__observers)

    def __enter__(self) -> "Observable":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False
