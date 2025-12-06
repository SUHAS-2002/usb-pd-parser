import json
from pathlib import Path
from datetime import datetime
import xlsxwriter


class ExcelValidationReport:
    """
    Generates a full validation Excel report from validation_report.json.
    Includes:
        - Summary sheet
        - Missing sections
        - Title mismatches
        - Page discrepancies
        - Quality statistics
        - Bar chart
    """

    def generate(self, report_json_path: str, output_xlsx: str):
        report_json_path = Path(report_json_path)
        output_xlsx = Path(output_xlsx)

        # Load validation JSON
        with report_json_path.open("r", encoding="utf-8") as f:
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

        match_percentage = round((matched / total) * 100, 2) if total else 0

        # =====================================================================
        # 1) SUMMARY SHEET
        # =====================================================================
        summary = workbook.add_worksheet("Summary")

        summary.write("A1", "USB PD VALIDATION REPORT", bold)
        summary.write("A3", "Generated On:")
        summary.write("B3", datetime.now().isoformat())

        summary.write_row(5, 0, ["Metric", "Value"], bold)

        rows = [
            ("Total TOC Sections", total),
            ("Matched Sections", matched),
            ("Match Percentage %", match_percentage),
            ("Missing Sections", missing),
            ("Title Mismatches", mismatches),
            ("Page Errors", page_errors),
            ("Quality Score %", quality_score),
        ]

        for i, (k, v) in enumerate(rows, start=6):
            summary.write(i, 0, k)
            summary.write(i, 1, v)

        # Add bar chart
        chart = workbook.add_chart({"type": "column"})
        chart.add_series({
            "categories": ["Summary", 6, 0, 12, 0],
            "values": ["Summary", 6, 1, 12, 1],
            "name": "Validation Metrics"
        })
        chart.set_title({"name": "Validation Overview"})
        summary.insert_chart("D5", chart)

        # =====================================================================
        # 2) Missing Sections Sheet
        # =====================================================================
        missing_ws = workbook.add_worksheet("Missing Sections")
        missing_ws.write_row(0, 0, ["Section ID", "Title", "Page"], bold)

        for row, m in enumerate(data.get("missing", []), start=1):
            missing_ws.write_row(row, 0, [
                m["section_id"],
                m["title"],
                m["page"]
            ])

        # =====================================================================
        # 3) Title Mismatches Sheet
        # =====================================================================
        mismatch_ws = workbook.add_worksheet("Title Mismatches")
        mismatch_ws.write_row(0, 0, ["Section ID", "TOC Title", "Chunk Title", "Similarity"], bold)

        for row, m in enumerate(data.get("title_mismatches", []), start=1):
            mismatch_ws.write_row(row, 0, [
                m["section_id"],
                m["toc_title"],
                m["chunk_title"],
                m["similarity"]
            ])

        # =====================================================================
        # 4) Page Errors Sheet
        # =====================================================================
        pages_ws = workbook.add_worksheet("Page Errors")
        pages_ws.write_row(0, 0, ["Section ID", "TOC Page", "Chunk Page Range"], bold)

        for row, p in enumerate(data.get("page_discrepancies", []), start=1):
            pages_ws.write_row(row, 0, [
                p["section_id"],
                p["toc_page"],
                str(p["chunk_range"])
            ])

        workbook.close()
        print(f"Validation Excel report saved → {output_xlsx}")
