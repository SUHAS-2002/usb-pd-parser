# src/validator/report_generator.py

import json
from dataclasses import dataclass
from typing import List, Dict
from pathlib import Path


# ------------------------------------------------------------
# Data model (immutable contract)
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# Report generator
# ------------------------------------------------------------
class ReportGenerator:
    """
    Generates validation scorecards and exports reports.

    Encapsulation rules:
    - Public methods delegate to private helpers
    - Scoring, persistence, and rendering are isolated
    """

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def generate(self, raw: Dict) -> ValidationReport:
        """
        Convert raw validator output into a ValidationReport.
        """
        metrics = self.__compute_metrics(raw)
        recommendations = self.__build_recommendations(metrics)

        return ValidationReport(
            quality_score=metrics["quality"],
            match_percentage=metrics["match_pct"],
            title_accuracy=metrics["title_pct"],
            page_accuracy=metrics["page_pct"],
            total_toc=metrics["total"],
            missing_count=metrics["missing"],
            mismatch_count=metrics["mismatch"],
            page_error_count=metrics["page_err"],
            recommendations=recommendations,
        )

    # ---------------------------------------------------------
    def save(
        self,
        report: ValidationReport,
        path: str = "data/score_report.json",
    ) -> None:
        self.__save_json(report, Path(path))
        print(f"Score report saved → {path}")

    # ---------------------------------------------------------
    def print_console(self, report: ValidationReport) -> None:
        self.__print_console(report)

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------
    def __compute_metrics(self, raw: Dict) -> Dict[str, float | int]:
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

        return {
            "quality": round(quality, 2),
            "match_pct": round(match_pct, 2),
            "title_pct": round(title_pct, 2),
            "page_pct": round(page_pct, 2),
            "total": total,
            "missing": missing,
            "mismatch": mismatch,
            "page_err": page_err,
        }

    # ---------------------------------------------------------
    def __build_recommendations(
        self,
        metrics: Dict[str, float | int],
    ) -> List[str]:
        recs: List[str] = []

        if metrics["missing"] > 0:
            recs.append(
                "Some TOC sections are missing in content. "
                "Improve chunk extraction."
            )

        if metrics["mismatch"] > 0:
            recs.append(
                "Section title mismatch detected. Improve parsing "
                "or adjust similarity threshold."
            )

        if metrics["page_err"] > 0:
            recs.append(
                "Section page boundaries appear inaccurate. "
                "Refine slicing logic."
            )

        if not recs:
            recs.append("Excellent extraction quality.")

        return recs

    # ---------------------------------------------------------
    def __save_json(
        self,
        report: ValidationReport,
        path: Path,
    ) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w", encoding="utf-8") as f:
            json.dump(
                report.__dict__,
                f,
                indent=2,
                ensure_ascii=False,
            )

    # ---------------------------------------------------------
    def __print_console(self, report: ValidationReport) -> None:
        print("\n============== VALIDATION REPORT ==============")
        print(f"Quality Score     : {report.quality_score}%")
        print(f"TOC Match         : {report.match_percentage}%")
        print(f"Title Accuracy    : {report.title_accuracy}%")
        print(f"Page Accuracy     : {report.page_accuracy}%")
        print(f"Total TOC Items   : {report.total_toc}")
        print(f"Missing Sections  : {report.missing_count}")
        print(f"Mismatched Titles : {report.mismatch_count}")
        print(f"Page Errors       : {report.page_error_count}")
        print("\nRecommendations:")
        for rec in report.recommendations:
            print(f"  - {rec}")
        print("================================================\n")
