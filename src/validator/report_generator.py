# src/validator/report_generator.py

import json
from dataclasses import dataclass
from typing import List, Dict


@dataclass
class ValidationReport:
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
    Converts validator raw data into:
        ✓ A readable scorecard
        ✓ Recommendations
        ✓ JSON output
    """

    def generate(self, raw: Dict) -> ValidationReport:

        total = raw["total_toc"]
        matched = len(raw["matched"])
        missing = len(raw["missing"])
        mismatch = len(raw["title_mismatches"])
        page_err = len(raw["page_discrepancies"])

        # Percentages
        match_pct = matched / total * 100 if total else 0
        title_pct = (1 - (mismatch / total)) * 100 if total else 0
        page_pct = (1 - (page_err / total)) * 100 if total else 0

        # Weighted quality score (tweakable)
        quality = (match_pct * 0.5) + (title_pct * 0.3) + (page_pct * 0.2)

        recs = []
        if missing > 0:
            recs.append("Some TOC sections missing in content. Improve chunk extraction.")
        if mismatch > 0:
            recs.append("Title mismatch detected. Improve parsing or adjust similarity threshold.")
        if page_err > 0:
            recs.append("Section boundaries need refinement.")
        if quality > 95:
            recs.append("Excellent extraction quality.")
        elif quality > 85:
            recs.append("Good quality, minor improvements possible.")
        else:
            recs.append("Extraction quality needs improvement.")

        return ValidationReport(
            quality_score=round(quality, 2),
            match_percentage=round(match_pct, 2),
            title_accuracy=round(title_pct, 2),
            page_accuracy=round(page_pct, 2),
            total_toc=total,
            missing_count=missing,
            mismatch_count=mismatch,
            page_error_count=page_err,
            recommendations=recs
        )

    # --------------------------------------------------------------
    def save(self, report: ValidationReport, path="score_report.json"):
        with open(path, "w", encoding="utf-8") as f:
            json.dump(report.__dict__, f, indent=2, ensure_ascii=False)

        print(f"Score report saved → {path}")

    # --------------------------------------------------------------
    def print_console(self, report: ValidationReport):
        print("\n================ VALIDATION REPORT ================")
        print(f"Quality Score     : {report.quality_score}%")
        print(f"TOC Match         : {report.match_percentage}%")
        print(f"Title Accuracy    : {report.title_accuracy}%")
        print(f"Page Boundary Acc : {report.page_accuracy}%")
        print(f"TOC Entries       : {report.total_toc}")
        print(f"Missing Sections  : {report.missing_count}")
        print(f"Mismatched Titles : {report.mismatch_count}")
        print(f"Page Errors       : {report.page_error_count}")
        print("\nRecommendations:")
        for r in report.recommendations:
            print(f"  - {r}")
        print("===================================================\n")
