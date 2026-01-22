# src/generators/spec_generator.py

import json
from pathlib import Path
from typing import List, Dict, Any

from src.utils.jsonl_utils import JSONLHandler
from src.core.base_generator import BaseGenerator


class SpecJSONLGenerator(BaseGenerator):
    """
    Builds the final USB PD specification JSONL file.

    IMPORTANT:
    - Writes ONLY content sections
    - No metadata header
    - No TOC duplication
    - No artificial 'type' field

    Encapsulation:
    - Internal state is fully private (name-mangled)
    - State exposed via validated properties
    """

    # ---------------------------------------------------------
    # Constructor + private state
    # ---------------------------------------------------------
    def __init__(self) -> None:
        self.__output_path: Path | None = None
        self.__records_written: int = 0

    # ---------------------------------------------------------
    # Properties (PHASE 3)
    # ---------------------------------------------------------
    @property
    def output_path(self) -> Path | None:
        """Get output file path (read-only)."""
        return self.__output_path

    @output_path.setter
    def output_path(self, value: str | Path) -> None:
        """Set output file path with validation."""
        path = Path(value)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.__output_path = path

    @property
    def records_written(self) -> int:
        """Get number of records written."""
        return self.__records_written

    @records_written.setter
    def records_written(self, value: int) -> None:
        """Set records written (must be non-negative)."""
        if not isinstance(value, int) or value < 0:
            raise ValueError("records_written must be a non-negative integer")
        self.__records_written = value

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def generate(
        self,
        toc_path: str,          # kept for interface compatibility
        chunks_path: str,
        output_path: str = "usb_pd_spec.jsonl",
    ) -> Path:
        """
        Generate JSONL file with only content sections.
        """
        # NOTE: toc_path intentionally unused (STEP 1 requirement)

        chunks: List[Dict[str, Any]] = JSONLHandler.load(
            Path(chunks_path)
        )

        self.output_path = output_path
        self.records_written = 0

        with self.output_path.open("w", encoding="utf-8") as f:
            for section in chunks:
                clean_section = {
                    key: value
                    for key, value in section.items()
                    if key != "type"
                }
                f.write(
                    json.dumps(
                        clean_section,
                        ensure_ascii=False,
                    )
                    + "\n"
                )
                self.records_written += 1

        print(f"Spec JSONL written → {self.output_path}")
        return self.output_path
    
    # ---------------------------------------------------------
    # Polymorphism: Special methods
    # ---------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"SpecJSONLGenerator(records={self.__records_written}, output={self.__output_path})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"SpecJSONLGenerator()"
    
    def __eq__(self, other: object) -> bool:
        """Equality based on output path and records."""
        if not isinstance(other, SpecJSONLGenerator):
            return NotImplemented
        return (
            self.__output_path == other.__output_path
            and self.__records_written == other.__records_written
        )
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.__class__, self.__output_path, self.__records_written))
    
    def __len__(self) -> int:
        """Return number of records written."""
        return self.__records_written
    
    def __bool__(self) -> bool:
        """Truthiness: True if has written records."""
        return self.__records_written > 0
    
    def __enter__(self) -> "SpecJSONLGenerator":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False