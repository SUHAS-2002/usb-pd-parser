# src/validator/toc_validator.py

import json
from pathlib import Path
from src.validator.matcher import SectionMatcher


class TOCValidator:
    """
    High-level validator that compares:
        TOC entries  ↔  Content chunks
    """

    def __init__(self, title_threshold: float = 0.85):
        self.matcher = SectionMatcher(title_threshold)

    def validate(self, toc_path: str, chunks_path: str, report_path="validation_report.json"):
        """
        Run validation and save a detailed diagnostics report.
        """
        toc = [json.loads(l) for l in open(toc_path, encoding="utf-8")]
        chunks = [json.loads(l) for l in open(chunks_path, encoding="utf-8")]

        report = self.matcher.match(toc, chunks)

        Path(report_path).write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        print(f"Validation report written to: {report_path}")
        return report
