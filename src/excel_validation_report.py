# src/excel_validation_report.py

import json
from pathlib import Path
from datetime import datetime
import xlsxwriter


class ExcelValidationReport:
    """
    Generates a full validation Excel report based on
    validation_report.json.

    Includes:
    - Summary sheet
    - Missing sections
    - Title mismatches
    - Page discrepancies
    - Quality scores
    - Column chart
    """

    def generate(self, report_json_path: str,
                 output_xlsx: str) -> None:
        """Generate a detailed Excel validation report."""
        report_json_path = Path(report_json_path)
        output_xlsx = Path(output_xlsx)

        with report_json_path.open(
            "r", encoding="utf-8"
        ) as f:
            data = json.load(f)

        workbook = xlsxwriter.Workbook(str(output_xlsx))
        bold = workbook.add_format({"bold": True})

        # Extract fields safely
        total = data.get("total_toc", 0)
        matched = len(data.get("matched", []))
        missing = len(data.get("missing", []))
        mismatches = len(data.get("title_mismatches", []))
        page_errors = len(data.get("page_discrepancies", []))
        quality_score = data.get("quality_score", 0)

        if total:
            match_pct = round((matched / total) * 100, 2)
        else:
            match_pct = 0

        # ============================================================
        # 1) SUMMARY SHEET
        # ============================================================
        summary = workbook.add_worksheet("Summary")

        summary.write("A1", "USB PD VALIDATION REPORT", bold)
        summary.write("A3", "Generated On:")
        summary.write("B3", datetime.now().isoformat())

        summary.write_row(5, 0, ["Metric", "Value"], bold)

        rows = [
            ("Total TOC Sections", total),
            ("Matched Sections", matched),
            ("Match Percentage %", match_pct),
            ("Missing Sections", missing),
            ("Title Mismatches", mismatches),
            ("Page Errors", page_errors),
            ("Quality Score %", quality_score),
        ]

        for idx, (label, value) in enumerate(rows, start=6):
            summary.write(idx, 0, label)
            summary.write(idx, 1, value)

        # Chart ------------------------------------------------------
        chart = workbook.add_chart({"type": "column"})
        chart.add_series(
            {
                "categories": ["Summary", 6, 0, 12, 0],
                "values": ["Summary", 6, 1, 12, 1],
                "name": "Validation Metrics",
            }
        )
        chart.set_title({"name": "Validation Overview"})
        summary.insert_chart("D5", chart)

        # ============================================================
        # 2) MISSING SECTIONS
        # ============================================================
        ws_missing = workbook.add_worksheet("Missing Sections")
        ws_missing.write_row(
            0, 0, ["Section ID", "Title", "Page"], bold
        )

        for row, sec in enumerate(
            data.get("missing", []), start=1
        ):
            ws_missing.write_row(
                row,
                0,
                [
                    sec["section_id"],
                    sec["title"],
                    sec["page"],
                ],
            )

        # ============================================================
        # 3) TITLE MISMATCHES
        # ============================================================
        ws_mismatch = workbook.add_worksheet(
            "Title Mismatches"
        )
        ws_mismatch.write_row(
            0,
            0,
            [
                "Section ID",
                "TOC Title",
                "Chunk Title",
                "Similarity",
            ],
            bold,
        )

        for row, mis in enumerate(
            data.get("title_mismatches", []), start=1
        ):
            ws_mismatch.write_row(
                row,
                0,
                [
                    mis["section_id"],
                    mis["toc_title"],
                    mis["chunk_title"],
                    mis["similarity"],
                ],
            )

        # ============================================================
        # 4) PAGE ERRORS
        # ============================================================
        ws_pages = workbook.add_worksheet("Page Errors")
        ws_pages.write_row(
            0,
            0,
            ["Section ID", "TOC Page", "Chunk Page Range"],
            bold,
        )

        for row, err in enumerate(
            data.get("page_discrepancies", []), start=1
        ):
            ws_pages.write_row(
                row,
                0,
                [
                    err["section_id"],
                    err["toc_page"],
                    str(err["chunk_range"]),
                ],
            )

        workbook.close()
        print(f"✔ Validation Excel report saved → {output_xlsx}")
