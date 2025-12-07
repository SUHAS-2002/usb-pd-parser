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

    def __init__(self, title_threshold: float = 0.85) -> None:
        self._matcher = SectionMatcher(title_threshold)

    # ---------------------------------------------------------
    def validate(
        self,
        toc_path: str,
        chunks_path: str,
        report_path: str = "validation_report.json"
    ) -> Dict:
        """
        Compare TOC entries with extracted content chunks and
        produce a validation report.

        Parameters
        ----------
        toc_path : str
            Path to TOC JSONL file.
        chunks_path : str
            Path to extracted section chunks JSONL file.
        report_path : str
            Output JSON report file path.

        Returns
        -------
        dict
            Raw match results from SectionMatcher.
        """

        toc = self._load_jsonl(Path(toc_path))
        chunks = self._load_jsonl(Path(chunks_path))

        result = self._matcher.match(toc, chunks)

        out = Path(report_path)
        out.write_text(
            json.dumps(result, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        print(f"Validation report saved → {out}")
        return result

    # ---------------------------------------------------------
    def _load_jsonl(self, path: Path) -> List[Dict]:
        """Load JSONL file into a list of dictionaries."""
        items: List[Dict] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        return items
