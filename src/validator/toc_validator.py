# src/validator/toc_validator.py

import json
from pathlib import Path
from typing import List, Dict

from src.validator.matcher import SectionMatcher


class TOCValidator:
    """
    Validates consistency between:
        - TOC entries
        - Extracted content chunks

    Encapsulation rules:
    - validate() is the ONLY public method
    - matching and I/O are encapsulated
    """

    # ---------------------------------------------------------
    # Construction (private state)
    # ---------------------------------------------------------
    def __init__(self, title_threshold: float = 0.85) -> None:
        self.__matcher = SectionMatcher(title_threshold)

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def validate(
        self,
        toc_path: str,
        chunks_path: str,
        report_path: str = "validation_report.json",
    ) -> Dict:
        toc = self.__load_jsonl(Path(toc_path))
        chunks = self.__load_jsonl(Path(chunks_path))

        result = self.__match(toc, chunks)
        self.__persist_report(result, Path(report_path))

        print(f"Validation report saved → {report_path}")
        return result

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------
    def __match(
        self,
        toc: List[Dict],
        chunks: List[Dict],
    ) -> Dict:
        return self.__matcher.match(toc, chunks)

    # ---------------------------------------------------------
    def __persist_report(
        self,
        report: Dict,
        path: Path,
    ) -> None:
        path.write_text(
            json.dumps(
                report,
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    # ---------------------------------------------------------
    def __load_jsonl(self, path: Path) -> List[Dict]:
        items: List[Dict] = []

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))

        return items
