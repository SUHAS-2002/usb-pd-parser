# src/validator/toc_validator.py

import json
from pathlib import Path
from typing import List, Dict

from src.validator.matcher import SectionMatcher


class TOCValidator:
    """
    Validates consistency between:
        • TOC entries
        • Extracted content chunks

    Responsibilities:
    - Load JSONL TOC + chunk files
    - Use SectionMatcher to compute discrepancies
    - Save validation report as JSON
    """

    # ---------------------------------------------------------
    def __init__(self, title_threshold: float = 0.85) -> None:
        self._title_threshold: float | None = None
        self._matcher: SectionMatcher | None = None

        self.title_threshold = title_threshold

    # ---------------------------------------------------------
    # Properties (Encapsulation)
    # ---------------------------------------------------------
    @property
    def title_threshold(self) -> float:
        """Return matcher title similarity threshold."""
        if self._title_threshold is None:
            raise ValueError("Title threshold not initialized.")
        return self._title_threshold

    @title_threshold.setter
    def title_threshold(self, value: float) -> None:
        if not 0.0 < value <= 1.0:
            raise ValueError(
                "title_threshold must be between 0 and 1"
            )
        self._title_threshold = value
        self._matcher = SectionMatcher(value)

    @property
    def matcher(self) -> SectionMatcher:
        """Return configured SectionMatcher instance."""
        if self._matcher is None:
            raise ValueError("Matcher not initialized.")
        return self._matcher

    # ---------------------------------------------------------
    # Public API (unchanged)
    # ---------------------------------------------------------
    def validate(
        self,
        toc_path: str,
        chunks_path: str,
        report_path: str = "validation_report.json",
    ) -> Dict:
        """
        Compare TOC entries with extracted content chunks and
        produce a validation report.
        """

        toc = self._load_jsonl(Path(toc_path))
        chunks = self._load_jsonl(Path(chunks_path))

        result = self.matcher.match(toc, chunks)

        out = Path(report_path)
        out.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print(f"Validation report saved → {out}")
        return result

    # ---------------------------------------------------------
    # Internals
    # ---------------------------------------------------------
    def _load_jsonl(self, path: Path) -> List[Dict]:
        """Load JSONL file into a list of dictionaries."""
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        items: List[Dict] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        return items
