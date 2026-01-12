# src/core/base_report_generator.py

"""
Abstract base class for all report generators.

Defines common interface and shared functionality,
promoting code reuse and polymorphism.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict
from datetime import datetime


class BaseReportGenerator(ABC):
    """
    Abstract base class for report generators.

    Implements Template Method pattern for report generation.
    """

    def __init__(self, output_path: str) -> None:
        self._output_path = Path(output_path)
        self._timestamp = datetime.now()

    # ---------------------------------------------------------
    # Properties (Encapsulation)
    # ---------------------------------------------------------
    @property
    def output_path(self) -> Path:
        """Get output file path."""
        return self._output_path

    @property
    def timestamp(self) -> datetime:
        """Get generation timestamp."""
        return self._timestamp

    # ---------------------------------------------------------
    # Template Method (defines algorithm skeleton)
    # ---------------------------------------------------------
    def generate(self) -> Path:
        """
        Generate report using template method pattern.

        Steps:
        1. Validate inputs
        2. Load data
        3. Process data
        4. Format output
        5. Save report
        6. Post-process

        Returns:
            Path to generated report
        """
        self._validate_inputs()
        data = self._load_data()
        processed = self._process_data(data)
        formatted = self._format_output(processed)
        output_path = self._save_report(formatted)
        self._post_process()
        return output_path

    # ---------------------------------------------------------
    # Abstract methods (must be implemented by subclasses)
    # ---------------------------------------------------------
    @abstractmethod
    def _validate_inputs(self) -> None:
        """Validate input files/parameters."""
        pass

    @abstractmethod
    def _load_data(self) -> Dict[str, Any]:
        """Load required data for report generation."""
        pass

    @abstractmethod
    def _process_data(self, data: Dict[str, Any]) -> Any:
        """Process loaded data."""
        pass

    @abstractmethod
    def _format_output(self, data: Any) -> Any:
        """Format data for output."""
        pass

    @abstractmethod
    def _save_report(self, formatted_data: Any) -> Path:
        """Save formatted report to file."""
        pass

    # ---------------------------------------------------------
    # Hook methods (optional override)
    # ---------------------------------------------------------
    def _post_process(self) -> None:
        """
        Optional post-processing after report generation.

        Subclasses can override to add custom behavior.
        """
        print(f"Report generated → {self.output_path}")

    # ---------------------------------------------------------
    # Utility methods (shared functionality)
    # ---------------------------------------------------------
    def _timestamped_filename(
        self,
        base_name: str,
        suffix: str,
    ) -> Path:
        """Create timestamped filename."""
        stamp = self._timestamp.strftime("%Y%m%d_%H%M%S")
        name = f"{base_name}_{stamp}{suffix}"
        return self._output_path.parent / name

    # ---------------------------------------------------------
    # Polymorphism (special methods)
    # ---------------------------------------------------------
    def __str__(self) -> str:
        return f"{self.__class__.__name__}(output={self.output_path.name})"

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}"
            f"(output_path={self.output_path!r})"
        )
