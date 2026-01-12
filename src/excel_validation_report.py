import json
from pathlib import Path
from typing import Dict, Any

import xlsxwriter

from src.core.base_report_generator import BaseReportGenerator


class ExcelValidationReport(BaseReportGenerator):
    """
    Generates a detailed Excel validation report.

    Sheets:
    - Summary
    - Missing Sections
    - Title Mismatches
    - Page Errors
    """

    # ------------------------------------------------------------------
    def __init__(self, report_json_path: str, output_xlsx: str) -> None:
        super().__init__(output_xlsx)
        self._report_json_path = Path(report_json_path)

    # ------------------------------------------------------------------
    # Special methods (Improvement 10)
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable description."""
        return (
            "ExcelValidationReport("
            f"report={self._report_json_path.name}"
            ")"
        )

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            "ExcelValidationReport("
            f"report_json_path={self._report_json_path!r}, "
            f"output_path={self.output_path!r}"
            ")"
        )

    def __eq__(self, other: object) -> bool:
        """Logical equality based on inputs."""
        if not isinstance(other, ExcelValidationReport):
            return NotImplemented
        return (
            self._report_json_path == other._report_json_path
            and self.output_path == other.output_path
        )

    def __len__(self) -> int:
        """Number of logical report sections."""
        return 4

    # ------------------------------------------------------------------
    # Context manager support (Improvement 9)
    # ------------------------------------------------------------------
    def __enter__(self) -> "ExcelValidationReport":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False

    def __del__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Template method steps
    # ------------------------------------------------------------------
    def _validate_inputs(self) -> None:
        if not self._report_json_path.exists():
            raise FileNotFoundError(
                f"Validation report not found: {self._report_json_path}"
            )

    def _load_data(self) -> Dict[str, Any]:
        with self._report_json_path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        total = data.get("total_toc", 0)
        matched = len(data.get("matched", []))
        missing = len(data.get("missing", []))
        mismatches = len(data.get("title_mismatches", []))
        page_errors = len(data.get("page_discrepancies", []))
        quality_score = data.get("quality_score", 0)

        match_pct = round((matched / total) * 100, 2) if total else 0

        return {
            "raw": data,
            "summary": {
                "total": total,
                "matched": matched,
                "missing": missing,
                "mismatches": mismatches,
                "page_errors": page_errors,
                "match_pct": match_pct,
                "quality_score": quality_score,
            },
        }

    def _format_output(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return data

    def _save_report(self, data: Dict[str, Any]) -> Path:
        final_output = self._timestamped_filename(
            self.output_path.stem,
            self.output_path.suffix,
        )

        workbook = xlsxwriter.Workbook(str(final_output))
        bold = workbook.add_format({"bold": True})

        self._write_summary_sheet(
            workbook, bold, data["summary"]
        )
        self._write_missing_sheet(
            workbook, bold, data["raw"]
        )
        self._write_title_mismatch_sheet(
            workbook, bold, data["raw"]
        )
        self._write_page_error_sheet(
            workbook, bold, data["raw"]
        )

        workbook.close()
        return final_output

    # ------------------------------------------------------------------
    # Extracted helper methods (SRP)
    # ------------------------------------------------------------------
    def _write_summary_sheet(
        self,
        workbook,
        bold,
        summary_data: Dict[str, Any],
    ) -> None:
        ws = workbook.add_worksheet("Summary")

        ws.write("A1", "USB PD VALIDATION REPORT", bold)
        ws.write("A3", "Generated On:")
        ws.write("B3", self.timestamp.isoformat())

        ws.write_row(5, 0, ["Metric", "Value"], bold)

        rows = [
            ("Total TOC Sections", summary_data["total"]),
            ("Matched Sections", summary_data["matched"]),
            ("Match Percentage %", summary_data["match_pct"]),
            ("Missing Sections", summary_data["missing"]),
            ("Title Mismatches", summary_data["mismatches"]),
            ("Page Errors", summary_data["page_errors"]),
            ("Quality Score %", summary_data["quality_score"]),
        ]

        for idx, (label, value) in enumerate(rows, start=6):
            ws.write(idx, 0, label)
            ws.write(idx, 1, value)

        self._add_summary_chart(ws, workbook)

    @staticmethod
    def _add_summary_chart(ws, workbook) -> None:
        chart = workbook.add_chart({"type": "column"})
        chart.add_series(
            {
                "categories": ["Summary", 6, 0, 12, 0],
                "values": ["Summary", 6, 1, 12, 1],
                "name": "Validation Metrics",
            }
        )
        chart.set_title({"name": "Validation Overview"})
        ws.insert_chart("D5", chart)

    @staticmethod
    def _write_missing_sheet(
        workbook, bold, raw: Dict[str, Any]
    ) -> None:
        ws = workbook.add_worksheet("Missing Sections")
        ws.write_row(0, 0, ["Section ID", "Title", "Page"], bold)

        for row, sec in enumerate(raw.get("missing", []), start=1):
            ws.write_row(
                row,
                0,
                [sec["section_id"], sec["title"], sec["page"]],
            )

    @staticmethod
    def _write_title_mismatch_sheet(
        workbook, bold, raw: Dict[str, Any]
    ) -> None:
        ws = workbook.add_worksheet("Title Mismatches")
        ws.write_row(
            0,
            0,
            ["Section ID", "TOC Title", "Chunk Title", "Similarity"],
            bold,
        )

        for row, mis in enumerate(
            raw.get("title_mismatches", []), start=1
        ):
            ws.write_row(
                row,
                0,
                [
                    mis["section_id"],
                    mis["toc_title"],
                    mis["chunk_title"],
                    mis["similarity"],
                ],
            )

    @staticmethod
    def _write_page_error_sheet(
        workbook, bold, raw: Dict[str, Any]
    ) -> None:
        ws = workbook.add_worksheet("Page Errors")
        ws.write_row(
            0,
            0,
            ["Section ID", "TOC Page", "Chunk Page Range"],
            bold,
        )

        for row, err in enumerate(
            raw.get("page_discrepancies", []), start=1
        ):
            ws.write_row(
                row,
                0,
                [
                    err["section_id"],
                    err["toc_page"],
                    str(err["chunk_range"]),
                ],
            )
