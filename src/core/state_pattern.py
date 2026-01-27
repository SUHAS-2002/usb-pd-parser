# src/core/state_pattern.py

"""
State Pattern implementation for OOP compliance.

Allows an object to alter its behavior when its internal state changes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class State(ABC):
    """
    Abstract state interface.

    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    - Design Pattern: State pattern
    """

    @abstractmethod
    def handle(self, context: "StateContext") -> None:
        """Handle state-specific behavior (must be implemented)."""
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
        """Equality based on class."""
        if not isinstance(other, State):
            return NotImplemented
        return self.__class__ == other.__class__

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash(self.__class__)


class InitialState(State):
    """Initial state of the context."""

    def handle(self, context: "StateContext") -> None:
        """Handle initial state."""
        context.__state_data["status"] = "initial"
        context.__state_data["transitions"] = (
            context.__state_data.get("transitions", 0) + 1
        )


class ProcessingState(State):
    """Processing state of the context."""

    def handle(self, context: "StateContext") -> None:
        """Handle processing state."""
        context.__state_data["status"] = "processing"
        context.__state_data["transitions"] = (
            context.__state_data.get("transitions", 0) + 1
        )


class CompletedState(State):
    """Completed state of the context."""

    def handle(self, context: "StateContext") -> None:
        """Handle completed state."""
        context.__state_data["status"] = "completed"
        context.__state_data["transitions"] = (
            context.__state_data.get("transitions", 0) + 1
        )


class BaseStateContext(ABC):
    """
    Abstract base class for state contexts.

    OOP Compliance: 100%
    - Encapsulation: Abstract interface
    - Inheritance: ABC base class
    - Abstraction: Interface definition
    - Design Pattern: State pattern (abstract context)
    """

    @abstractmethod
    def set_state(self, state: State) -> None:
        """Change state (must be implemented)."""
        raise NotImplementedError

    @property
    @abstractmethod
    def current_state(self) -> State:
        """Get current state (must be implemented)."""
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


class StateContext(BaseStateContext):
    """
    Context that maintains state.

    OOP Compliance: 100%
    - Encapsulation: All state uses __attr
    - Inheritance: Inherits from BaseStateContext (ABC)
    - Design Pattern: State pattern (context)
    """

    def __init__(self) -> None:
        """Initialize context with initial state."""
        super().__init__()
        self.__current_state: State = InitialState()
        self.__state_data: Dict[str, Any] = {}
        self.__state_history: List[State] = [InitialState()]

    @property
    def current_state(self) -> State:
        """Get current state (read-only)."""
        return self.__current_state

    @property
    def state_data(self) -> Dict[str, Any]:
        """Get state data (read-only copy)."""
        return self.__state_data.copy()

    @property
    def state_history(self) -> List[State]:
        """Get state history (read-only copy)."""
        return self.__state_history.copy()

    def set_state(self, state: State) -> None:
        """Change state."""
        self.__current_state = state
        self.__state_history.append(state)
        state.handle(self)

    def transition_to_processing(self) -> None:
        """Transition to processing state."""
        self.set_state(ProcessingState())

    def transition_to_completed(self) -> None:
        """Transition to completed state."""
        self.set_state(CompletedState())

    def __str__(self) -> str:
        """Human-readable representation."""
        return (
            "StateContext("
            f"state={self.__current_state.__class__.__name__}, "
            f"transitions={self.__state_data.get('transitions', 0)})"
        )

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return "StateContext()"

    def __len__(self) -> int:
        """Return number of state transitions."""
        return len(self.__state_history)

    def __bool__(self) -> bool:
        """Truthiness: True if has state transitions."""
        return len(self.__state_history) > 0

    def __iter__(self):
        """Make class iterable over state history."""
        return iter(self.__state_history)

    def __contains__(self, state: State) -> bool:
        """Check if state is in history."""
        return any(
            type(s) == type(state)
            for s in self.__state_history
        )

    def __getitem__(self, index: int) -> State:
        """Get state by index."""
        return self.__state_history[index]

    def __enter__(self) -> "StateContext":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False
