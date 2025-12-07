# src/validator/report_generator.py

import json
from dataclasses import dataclass
from typing import List, Dict
from pathlib import Path


@dataclass
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


class ReportGenerator:
    """
    Generates a human-readable validation scorecard and produces
    JSON reports for external tools.
    """

    def generate(self, raw: Dict) -> ValidationReport:
        """Convert raw validator output into a score object."""
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

        return ValidationReport(
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

    # ----------------------------------------------------------
    def save(
        self,
        report: ValidationReport,
        path: str = "data/score_report.json"
    ) -> None:
        """Save report as JSON inside data/ folder."""
        output = Path(path)

        # Ensure directory exists
        output.parent.mkdir(parents=True, exist_ok=True)

        with output.open("w", encoding="utf-8") as f:
            json.dump(report.__dict__, f, indent=2,
                      ensure_ascii=False)

        print(f"Score report saved → {output}")

    # ----------------------------------------------------------
    def print_console(self, report: ValidationReport) -> None:
        """Pretty-print the scorecard to console."""
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
