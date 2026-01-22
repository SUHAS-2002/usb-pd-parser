import json
from pathlib import Path
from typing import Dict, Any, Optional

from src.validator.matcher import SectionMatcher
from src.utils.jsonl_utils import JSONLHandler
from src.config import CONFIG
from src.core.base_validator import BaseValidator


class TOCValidator(BaseValidator):
    """
    Validates consistency between:
        • TOC entries
        • Extracted content chunks

    Responsibilities:
    - Load JSONL TOC + chunk files
    - Delegate comparison to SectionMatcher
    - Save validation report as JSON AND JSONL

    Encapsulation:
    - Public API: validate()
    - ALL internal state uses name-mangled attributes (__attr)
    """

    # ---------------------------------------------------------
    # Constructor (TRUE PRIVATE STATE)
    # ---------------------------------------------------------
    def __init__(
        self,
        matcher: Optional[SectionMatcher] = None,
        title_threshold: Optional[float] = None,
    ) -> None:
        """Initialize validator with dependency injection."""
        if matcher is not None:
            self.__matcher: SectionMatcher = matcher
        else:
            threshold = (
                title_threshold
                if title_threshold is not None
                else CONFIG.validation.TITLE_SIMILARITY
            )
            self.__matcher = SectionMatcher(threshold)

    # ---------------------------------------------------------
    # Encapsulation
    # ---------------------------------------------------------
    @property
    def matcher(self) -> SectionMatcher:
        """Return matcher instance (read-only)."""
        return self.__matcher

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def validate(
        self,
        toc_path: str,
        chunks_path: str,
        report_path: str = "validation_report.json",
    ) -> Dict[str, Any]:
        """
        Compare TOC entries with extracted content chunks and
        produce validation reports.

        Outputs:
        - validation_report.json   (PRIMARY)
        - validation_report.jsonl  (compatibility)
        """
        toc = JSONLHandler.load(Path(toc_path))
        chunks = JSONLHandler.load(Path(chunks_path))

        result = self.__matcher.match(toc, chunks)

        output_path = self._normalize_report_path(report_path)

        self._write_json_report(output_path, result)
        self._write_jsonl_report(output_path, result)
        self._notify_user(output_path)

        return result

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------
    @staticmethod
    def _normalize_report_path(path: str) -> Path:
        output_path = Path(path)
        if output_path.suffix != ".json":
            output_path = output_path.with_suffix(".json")
        return output_path

    @staticmethod
    def _write_json_report(
        output_path: Path,
        result: Dict[str, Any],
    ) -> None:
        output_path.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    @staticmethod
    def _write_jsonl_report(
        output_path: Path,
        result: Dict[str, Any],
    ) -> None:
        jsonl_path = output_path.with_suffix(".jsonl")
        with jsonl_path.open("w", encoding="utf-8") as handle:
            handle.write(
                json.dumps(result, ensure_ascii=False) + "\n"
            )

    @staticmethod
    def _notify_user(output_path: Path) -> None:
        jsonl_path = output_path.with_suffix(".jsonl")
        print(f"Validation report saved → {output_path}")
        print(f"Validation report (JSONL) saved → {jsonl_path}")
    
    # ---------------------------------------------------------
    # Polymorphism: Special methods
    # ---------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable representation."""
        return f"TOCValidator(matcher={self.__matcher!r})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"TOCValidator()"
    
    def __eq__(self, other: object) -> bool:
        """Equality based on matcher."""
        if not isinstance(other, TOCValidator):
            return NotImplemented
        return self.__matcher == other.__matcher
    
    def __hash__(self) -> int:
        """Hash for use in sets/dicts."""
        return hash((self.__class__, self.__matcher))
    
    def __bool__(self) -> bool:
        """Truthiness: Always True (validator is always valid)."""
        return True
    
    def __enter__(self) -> "TOCValidator":
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False