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
    # Properties
    # ------------------------------------------------------------------
    @property
    def raw_validation(self) -> Dict[str, Any]:
        return self.__raw

    @property
    def report(self) -> ValidationReport | None:
        return self.__report

    # ------------------------------------------------------------------
    # Template method steps
    # ------------------------------------------------------------------
    def _validate_inputs(self) -> None:
        if not isinstance(self.__raw, dict):
            raise TypeError("Raw validation data must be a dictionary.")

    def _load_data(self) -> Dict[str, Any]:
        return self.__raw

    # --------------------------------------------------------------
    # REFACTORED: short orchestrator
    # --------------------------------------------------------------
    def _process_data(self, raw: Dict[str, Any]) -> ValidationReport:
        metrics = self._extract_metrics(raw)
        scores = self._calculate_scores(metrics)
        recs = self._build_recommendations(metrics)
        self.__report = self._build_report(metrics, scores, recs)
        return self.__report

    # --------------------------------------------------------------
    # Metrics & scoring helpers
    # --------------------------------------------------------------
    @staticmethod
    def _extract_metrics(raw: Dict[str, Any]) -> Dict[str, int]:
        return {
            "total": raw.get("total_toc", 0),
            "matched": len(raw.get("matched", [])),
            "missing": len(raw.get("missing", [])),
            "mismatch": len(raw.get("title_mismatches", [])),
            "page_err": len(raw.get("page_discrepancies", [])),
        }

    @staticmethod
    def _calculate_scores(metrics: Dict[str, int]) -> Dict[str, float]:
        total = metrics["total"]

        match_pct = (metrics["matched"] / total * 100) if total else 0
        title_pct = (1 - metrics["mismatch"] / total) * 100 if total else 0
        page_pct = (1 - metrics["page_err"] / total) * 100 if total else 0

        quality = (
            match_pct * 0.5 +
            title_pct * 0.3 +
            page_pct * 0.2
        )

        return {
            "match_pct": round(match_pct, 2),
            "title_pct": round(title_pct, 2),
            "page_pct": round(page_pct, 2),
            "quality": round(quality, 2),
        }

    # --------------------------------------------------------------
    # Recommendation engine
    # --------------------------------------------------------------
    @staticmethod
    def _build_recommendations(metrics: Dict[str, int]) -> List[str]:
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

    # --------------------------------------------------------------
    # Report construction
    # --------------------------------------------------------------
    @staticmethod
    def _build_report(
        metrics: Dict[str, int],
        scores: Dict[str, float],
        recs: List[str],
    ) -> ValidationReport:
        return ValidationReport(
            quality_score=scores["quality"],
            match_percentage=scores["match_pct"],
            title_accuracy=scores["title_pct"],
            page_accuracy=scores["page_pct"],
            total_toc=metrics["total"],
            missing_count=metrics["missing"],
            mismatch_count=metrics["mismatch"],
            page_error_count=metrics["page_err"],
            recommendations=recs,
        )

    # ------------------------------------------------------------------
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
