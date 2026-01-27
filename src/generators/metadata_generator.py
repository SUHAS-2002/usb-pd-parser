# src/generators/metadata_generator.py

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from src.utils.jsonl_utils import JSONLHandler
from src.core.base_generator import BaseGenerator


class MetadataGenerator(BaseGenerator):
    """
    Generates a single metadata JSON file summarizing:
        - Tool version
        - Timestamp
        - TOC count
        - Section count
        - Coverage percentage
    """

    # -------------------------------------------------------------
    # Private class constants (PHASE 2)
    # -------------------------------------------------------------
    __TOOL_VERSION: str = "1.0.0"

    # -------------------------------------------------------------
    # Constructor + private instance state (PHASE 3)
    # -------------------------------------------------------------
    def __init__(self) -> None:
        self.__output_path: Path | None = None
        self.__generated_at: datetime | None = None

    # -------------------------------------------------------------
    # Controlled access to constants
    # -------------------------------------------------------------
    @classmethod
    def _get_tool_version(cls) -> str:
        """Return tool version (protected access)."""
        return cls.__TOOL_VERSION

    # -------------------------------------------------------------
    # Properties (PHASE 3)
    # -------------------------------------------------------------
    @property
    def output_path(self) -> Path | None:
        """Get last generated metadata file path."""
        return self.__output_path

    @property
    def generated_at(self) -> datetime | None:
        """Get metadata generation timestamp."""
        return self.__generated_at

    # -------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------
    def generate(
        self,
        toc_path: str,
        chunks_path: str,
        output_path: str = "usb_pd_metadata.jsonl",
    ) -> Path:
        """Load TOC + chunks and write a metadata JSON file."""

        toc: List[Dict[str, Any]] = JSONLHandler.load(
            Path(toc_path)
        )
        chunks: List[Dict[str, Any]] = JSONLHandler.load(
            Path(chunks_path)
        )

        coverage = (
            (len(chunks) / len(toc)) * 100
            if toc
            else 0.0
        )

        self.__generated_at = datetime.now()
        self.__output_path = Path(output_path)

        metadata = {
            "type": "metadata",
            "tool_version": self._get_tool_version(),
            "generated_at": self.__generated_at.isoformat(),
            "toc_count": len(toc),
            "section_count": len(chunks),
            "coverage_percentage": round(coverage, 2),
        }

        with self.__output_path.open("w", encoding="utf-8") as f:
            json.dump(
                metadata,
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"Metadata JSON written → {self.__output_path}")
        return self.__output_path

    # -------------------------------------------------------------
    # Polymorphism: Special methods
    # -------------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation."""
        return (
            "MetadataGenerator("
            f"output={self.__output_path}, "
            f"generated={self.__generated_at})"
        )

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return "MetadataGenerator()"

    def __eq__(self, other: object) -> bool:
        """Equality based on output path."""
        if not isinstance(other, MetadataGenerator):
            return NotImplemented
        return self.__output_path == other.__output_path

    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.__class__, self.__output_path))

    def __bool__(self) -> bool:
        """Truthiness: True if has generated metadata."""
        return self.__output_path is not None

    def __enter__(self) -> "MetadataGenerator":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False
