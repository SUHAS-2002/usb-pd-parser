# src/validator/report_generator.py

import json
from dataclasses import dataclass
from typing import List, Dict, Any
from pathlib import Path

from src.core.base_report_generator import BaseReportGenerator


# ------------------------------------------------------------------
# Domain model
# ------------------------------------------------------------------
@dataclass(frozen=True)
class ValidationReport:
    """Structured score output for validation results."""
    quality_score: float
    match_percentage: float
    title_accuracy: float
    page_accuracy: float
    total_toc: int
    missing_count: int
    mismatch_count: int
    page_error_count: int
    recommendations: List[str]

    def __str__(self) -> str:
        return (
            f"ValidationReport("
            f"quality={self.quality_score}%, "
            f"match={self.match_percentage}%, "
            f"title={self.title_accuracy}%, "
            f"page={self.page_accuracy}%"
            f")"
        )

    def __repr__(self) -> str:
        return (
            "ValidationReport("
            f"quality_score={self.quality_score}, "
            f"match_percentage={self.match_percentage}, "
            f"title_accuracy={self.title_accuracy}, "
            f"page_accuracy={self.page_accuracy}, "
            f"total_toc={self.total_toc}"
            ")"
        )

    def __len__(self) -> int:
        return len(self.recommendations)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ValidationReport):
            return NotImplemented
        return (
            self.quality_score == other.quality_score
            and self.match_percentage == other.match_percentage
            and self.total_toc == other.total_toc
        )


# ------------------------------------------------------------------
# Generator
# ------------------------------------------------------------------
class ReportGenerator(BaseReportGenerator):
    """
    Generates a validation scorecard, prints it to console,
    and saves it as JSON.

    Fully compliant with BaseReportGenerator (LSP, OCP).
    """

    # ------------------------------------------------------------------
    def __init__(
        self,
        raw_validation: Dict[str, Any],
        output_path: str = "data/score_report.jsonl",
    ) -> None:
        super().__init__(output_path)
        self.__raw: Dict[str, Any] = raw_validation
        self.__report: ValidationReport | None = None

    # ------------------------------------------------------------------
    # Properties (PHASE 3)
    # ------------------------------------------------------------------
    @property
    def raw_validation(self) -> Dict[str, Any]:
        """Return raw validation input (read-only)."""
        return self.__raw

    @property
    def report(self) -> ValidationReport | None:
        """Return generated validation report (read-only)."""
        return self.__report

    # ------------------------------------------------------------------
    # Template method steps
    # ------------------------------------------------------------------
    def _validate_inputs(self) -> None:
        if not isinstance(self.__raw, dict):
            raise TypeError("Raw validation data must be a dictionary.")

    def _load_data(self) -> Dict[str, Any]:
        return self.__raw

    def _process_data(self, raw: Dict[str, Any]) -> ValidationReport:
        total = raw.get("total_toc", 0)
        matched = len(raw.get("matched", []))
        missing = len(raw.get("missing", []))
        mismatch = len(raw.get("title_mismatches", []))
        page_err = len(raw.get("page_discrepancies", []))

        match_pct = (matched / total * 100) if total else 0
        title_pct = (1 - mismatch / total) * 100 if total else 0
        page_pct = (1 - page_err / total) * 100 if total else 0

        quality = (
            match_pct * 0.5 +
            title_pct * 0.3 +
            page_pct * 0.2
        )

        recs: List[str] = []

        if missing > 0:
            recs.append(
                "Some TOC sections are missing in content. Improve "
                "chunk extraction."
            )

        if mismatch > 0:
            recs.append(
                "Section title mismatch detected. Improve parsing or "
                "adjust similarity threshold."
            )

        if page_err > 0:
            recs.append(
                "Section page boundaries appear inaccurate. Refine "
                "slicing logic."
            )

        if not recs:
            recs.append("Excellent extraction quality.")

        self.__report = ValidationReport(
            quality_score=round(quality, 2),
            match_percentage=round(match_pct, 2),
            title_accuracy=round(title_pct, 2),
            page_accuracy=round(page_pct, 2),
            total_toc=total,
            missing_count=missing,
            mismatch_count=mismatch,
            page_error_count=page_err,
            recommendations=recs,
        )

        return self.__report

    def _format_output(self, report: ValidationReport) -> Dict[str, Any]:
        return report.__dict__

    def _save_report(self, formatted: Dict[str, Any]) -> Path:
        output = self.output_path
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", encoding="utf-8") as f:
            json.dump(
                formatted,
                f,
                indent=2,
                ensure_ascii=False,
            )

        return output

    # ------------------------------------------------------------------
    # Hook: console output
    # ------------------------------------------------------------------
    def _post_process(self) -> None:
        if not self.__report:
            return

        r = self.__report
        print("\n============== VALIDATION REPORT ==============")
        print(f"Quality Score     : {r.quality_score}%")
        print(f"TOC Match         : {r.match_percentage}%")
        print(f"Title Accuracy    : {r.title_accuracy}%")
        print(f"Page Accuracy     : {r.page_accuracy}%")
        print(f"Total TOC Items   : {r.total_toc}")
        print(f"Missing Sections  : {r.missing_count}")
        print(f"Mismatched Titles : {r.mismatch_count}")
        print(f"Page Errors       : {r.page_error_count}")
        print("\nRecommendations:")
        for rec in r.recommendations:
            print(f"  - {rec}")
        print("================================================\n")
