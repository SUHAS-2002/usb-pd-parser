# src/core/base_generator.py

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any


class BaseGenerator(ABC):
    """
    Abstract base class for all generators.

    Provides common functionality for JSONL/JSON generation.
    All internal state uses name mangling (__attr) for true privacy.
    """

    def __init__(self) -> None:
        """Initialize generator with private state."""
        self.__generated_count: int = 0
        self.__output_path: Path | None = None

    # ---------------------------------------------------------
    # Encapsulation: Properties (read-only)
    # ---------------------------------------------------------
    @property
    def generated_count(self) -> int:
        """Get number of items generated (read-only)."""
        return self.__generated_count

    @property
    def output_path(self) -> Path | None:
        """Get output path (read-only)."""
        return self.__output_path

    # ---------------------------------------------------------
    # Abstract method
    # ---------------------------------------------------------
    @abstractmethod
    def generate(
        self,
        *args: Any,
        **kwargs: Any,
    ) -> Path:
        """Generate output (must be implemented by subclasses)."""
        raise NotImplementedError

    # ---------------------------------------------------------
    # Protected helpers
    # ---------------------------------------------------------
    def _increment_count(self) -> None:
        """Increment generation counter (protected)."""
        self.__generated_count += 1

    def _set_output_path(self, path: Path) -> None:
        """Set output path (protected)."""
        self.__output_path = path

    # ---------------------------------------------------------
    # Polymorphism: Special methods
    # ---------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation."""
        return (
            f"{self.__class__.__name__}("
            f"count={self.__generated_count}, "
            f"output={self.__output_path})"
        )

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"{self.__class__.__name__}()"

    def __len__(self) -> int:
        """Return number of items generated."""
        return self.__generated_count

    def __bool__(self) -> bool:
        """Truthiness: True if has generated items."""
        return self.__generated_count > 0

    def __eq__(self, other: object) -> bool:
        """Equality based on class and generated count."""
        if not isinstance(other, BaseGenerator):
            return NotImplemented
        return (
            self.__class__ == other.__class__
            and self.__generated_count == other.generated_count
        )

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.__class__, self.__generated_count))

    def __iter__(self):
        """Make class iterable (context-dependent)."""
        return iter([])

    def __contains__(self, item: Any) -> bool:
        """Check if item exists (context-dependent)."""
        return False

    def __getitem__(self, key: Any) -> Any:
        """Get item by key (context-dependent)."""
        raise KeyError(f"Key {key} not found")

    def __call__(self, *args: Any, **kwargs: Any) -> Path:
        """Make class callable - delegates to generate()."""
        return self.generate(*args, **kwargs)

    def __enter__(self) -> "BaseGenerator":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False

    def __del__(self) -> None:
        """Destructor for cleanup."""
        pass
