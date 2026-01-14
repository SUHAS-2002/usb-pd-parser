# src/generators/spec_generator.py

import json
from pathlib import Path
from typing import List, Dict, Any

from src.utils.jsonl_utils import JSONLHandler


class SpecJSONLGenerator:
    """
    Builds the final USB PD specification JSONL file.

    IMPORTANT:
    - Writes ONLY content sections
    - No metadata header
    - No TOC duplication
    - No artificial 'type' field

    Encapsulation:
    - Internal state is private
    - State exposed via read-only properties
    """

    # ---------------------------------------------------------
    # Constructor + private state (FIX 1.2)
    # ---------------------------------------------------------
    def __init__(self) -> None:
        self._output_path: Path | None = None
        self._records_written: int = 0

    # ---------------------------------------------------------
    # Read-only properties (FIX 1.2)
    # ---------------------------------------------------------
    @property
    def output_path(self) -> Path | None:
        """Return output file path."""
        return self._output_path

    @property
    def records_written(self) -> int:
        """Return number of records written."""
        return self._records_written

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

        self._output_path = Path(output_path)
        self._records_written = 0

        with self._output_path.open("w", encoding="utf-8") as f:
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
                self._records_written += 1

        print(f"Spec JSONL written → {self._output_path}")
        return self._output_path
