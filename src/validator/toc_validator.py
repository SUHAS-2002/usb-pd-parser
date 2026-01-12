import json
from pathlib import Path
from typing import Dict, Any, Optional

from src.validator.matcher import SectionMatcher
from src.utils.jsonl_utils import JSONLHandler
from src.config import CONFIG


class TOCValidator:
    """
    Validates consistency between:
        • TOC entries
        • Extracted content chunks

    Responsibilities:
    - Load JSONL TOC + chunk files
    - Delegate comparison to SectionMatcher
    - Save validation report as JSON

    Fully DIP-compliant:
    - Matcher is injectable
    - Default matcher is lazily constructed
    """

    # ---------------------------------------------------------
    def __init__(
        self,
        matcher: Optional[SectionMatcher] = None,
        title_threshold: Optional[float] = None,
    ) -> None:
        """
        Initialize validator with dependency injection.

        Args:
            matcher: Optional custom SectionMatcher instance
            title_threshold: Optional similarity threshold override
        """

        if matcher is not None:
            self._matcher = matcher
        else:
            threshold = (
                title_threshold
                if title_threshold is not None
                else CONFIG.validation.TITLE_SIMILARITY
            )
            self._matcher = SectionMatcher(threshold)

    # ---------------------------------------------------------
    # Encapsulation
    # ---------------------------------------------------------
    @property
    def matcher(self) -> SectionMatcher:
        """Return matcher instance."""
        return self._matcher

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
        produce a validation report.
        """

        toc = JSONLHandler.load(Path(toc_path))
        chunks = JSONLHandler.load(Path(chunks_path))

        result = self.matcher.match(toc, chunks)

        output = Path(report_path)
        output.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

        print(f"Validation report saved → {output}")
        return result
