import json
from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class Report:
    """Represents a validation report with quality metrics."""
    quality_score: float
    match_percentage: float
    recommendations: List[str]
    matched: List
    total_toc: int
    title_mismatches: List
    out_of_order: List
    page_discrepancies: List

class ReportGenerator:
    """Generates and saves validation reports with console output."""
    
    def _calculate_quality_score(self, data: Dict) -> float:
        total = data["total_toc"]
        if total == 0:
            return 0.0

        match_pct = len(data["matched"]) / total * 100
        score = match_pct * 0.6
        score += (100 - len(data["title_mismatches"]) / total * 100) * 0.2
        score += (100 - len(data["out_of_order"]) / total * 100) * 0.1
        score += (100 - len(data["page_discrepancies"]) / total * 100) * 0.1
        return round(max(0, score), 2)

    def _generate_recommendation(self, key: str, match_pct: float) -> str:
        recommendations = {
            "low_coverage": (
                f"Only {match_pct:.1f}% coverage — fix missing sections"
            ),
            "title_mismatches": "Title extraction needs improvement",
            "out_of_order": "Check PDF structure for out-of-order sections",
            "page_discrepancies": "Page numbers off — adjust offset logic",
            "perfect": "Perfect extraction! Ready for production."
        }
        return recommendations[key]

    def _build_recommendations(self, data: Dict) -> List[str]:
        recs = []
        match_pct = len(data["matched"]) / data["total_toc"] * 100

        if match_pct < 95:
            recs.append(self._generate_recommendation("low_coverage", match_pct))
        if data["title_mismatches"]:
            recs.append(self._generate_recommendation("title_mismatches", match_pct))
        if data["out_of_order"]:
            recs.append(self._generate_recommendation("out_of_order", match_pct))
        if data["page_discrepancies"]:
            recs.append(self._generate_recommendation("page_discrepancies", match_pct))
        if not recs:
            recs.append(self._generate_recommendation("perfect", match_pct))
        
        return recs

    def build_report(self, data: Dict, toc: List, chunks: List) -> Report:
        score = self._calculate_quality_score(data)
        match_pct = len(data["matched"]) / len(toc) * 100

        return Report(
            quality_score=score,
            match_percentage=match_pct,
            recommendations=self._build_recommendations(data),
            matched=data["matched"],
            total_toc=data["total_toc"],
            title_mismatches=data["title_mismatches"],
            out_of_order=data["out_of_order"],
            page_discrepancies=data["page_discrepancies"]
        )

class ReportWriter:
    """Handles saving and printing of reports."""
    
    def __init__(self, output_path: str):
        self.output_path = output_path

    def _get_status(self, quality_score: float) -> str:
        if quality_score >= 95:
            return "EXCELLENT"
        if quality_score >= 85:
            return "GOOD"
        return "NEEDS WORK"

    def save(self, report: Report):
        summary = {
            "summary": {
                "quality_score": report.quality_score,
                "match_percentage": report.match_percentage,
                "status": self._get_status(report.quality_score),
            },
            "recommendations": report.recommendations,
            "timestamp": datetime.now().isoformat(),
        }
        with open(self.output_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

    def print_summary(self, report: Report):
        print("\n" + "=" * 70)
        print("VALIDATION COMPLETE")
        print(f"Quality Score: {report.quality_score:.1f}/100")
        print(f"Match Rate: {report.match_percentage:.1f}%")
        print("\nRecommendations:")
        for rec in report.recommendations:
            print(f"  • {rec}")
        print("=" * 70 + "\n")

def main():
    sample_data = {
        "matched": [1, 2, 3],
        "total_toc": 5,
        "title_mismatches": [],
        "out_of_order": [4],
        "page_discrepancies": []
    }
    generator = ReportGenerator()
    report = generator.build_report(sample_data, [1, 2, 3, 4, 5], [])
    writer = ReportWriter("report.json")
    writer.save(report)
    writer.print_summary(report)

if __name__ == "__main__":
    main()
