import json
from typing import Dict, Any, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates final report and console output."""

    def _quality_score(self, data: Dict) -> float:
        total = data["total_toc"]
        if total == 0:
            return 0.0

        match_pct = len(data["matched"]) / total * 100
        score = match_pct * 0.6

        score += (100 - len(data["title_mismatches"]) / total * 100) * 0.2
        score += (100 - len(data["out_of_order"]) / total * 100) * 0.1
        score += (100 - len(data["page_discrepancies"]) / total * 100) * 0.1

        return round(max(0, score), 2)

    def _recommendations(self, data: Dict) -> List[str]:
        recs = []
        match_pct = len(data["matched"]) / data["total_toc"] * 100

        if match_pct < 95:
            recs.append(f"Only {match_pct:.1f}% coverage — fix missing sections")
        if data["title_mismatches"]:
            recs.append("Title extraction needs improvement")
        if data["out_of_order"]:
            recs.append("Sections out of order — check PDF structure")
        if data["page_discrepancies"]:
            recs.append("Page numbers drifting — adjust offset logic")
        if not recs:
            recs.append("Perfect extraction! Ready for production.")

        return recs

    def build_report(self, data: Dict, toc: List, chunks: List) -> Any:
        from dataclasses import dataclass

        @dataclass
        class Report:
            quality_score: float
            match_percentage: float
            recommendations: List[str]
            # ... other fields

        score = self._quality_score(data)
        return Report(
            quality_score=score,
            match_percentage=len(data["matched"]) / len(toc) * 100,
            recommendations=self._recommendations(data),
            # attach full data if needed
            **data
        )

    def save_and_print(self, report: Any, path: str):
        summary = {
            "summary": {
                "quality_score": report.quality_score,
                "match_percentage": report.match_percentage,
                "status": "EXCELLENT" if report.quality_score >= 95 else "GOOD"
                          if report.quality_score >= 85 else "NEEDS WORK",
            },
            "recommendations": report.recommendations,
            "timestamp": datetime.now().isoformat(),
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        print("\n" + "=" * 70)
        print("VALIDATION COMPLETE")
        print(f"Quality Score: {report.quality_score:.1f}/100")
        print(f"Match Rate: {report.match_percentage:.1f}%")
        print("\nRecommendations:")
        for r in report.recommendations:
            print(f"  • {r}")
        print("=" * 70 + "\n")