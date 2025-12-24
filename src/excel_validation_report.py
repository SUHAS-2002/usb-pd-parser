# src/excel_validation_report.py

import json
from pathlib import Path
from datetime import datetime
import xlsxwriter
from typing import Dict, Any


class ExcelValidationReport:
    """
    Generates a full validation Excel report from validation_report.json.

    Encapsulation rules:
    - generate() is the ONLY public method
    - workbook creation and rendering are private
    """

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def generate(
        self,
        report_json_path: str,
        output_xlsx: str,
    ) -> None:
        self.__report_path = Path(report_json_path)
        self.__output_path = Path(output_xlsx)

        data = self.__load_report()
        workbook = self.__create_workbook()

        self.__build_summary_sheet(workbook, data)
        self.__build_missing_sheet(workbook, data)
        self.__build_mismatch_sheet(workbook, data)
        self.__build_page_error_sheet(workbook, data)

        workbook.close()
        print(
            f"✔ Validation Excel report saved → "
            f"{self.__output_path}"
        )

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------
    def __load_report(self) -> Dict[str, Any]:
        with self.__report_path.open(
            "r", encoding="utf-8"
        ) as f:
            return json.load(f)

    # ---------------------------------------------------------
    def __create_workbook(self):
        return xlsxwriter.Workbook(str(self.__output_path))

    # ---------------------------------------------------------
    def __build_summary_sheet(
        self,
        workbook,
        data: Dict[str, Any],
    ) -> None:
        bold = workbook.add_format({"bold": True})
        summary = workbook.add_worksheet("Summary")

        total = data.get("total_toc", 0)
        matched = len(data.get("matched", []))
        missing = len(data.get("missing", []))
        mismatches = len(data.get("title_mismatches", []))
        page_errors = len(data.get("page_discrepancies", []))
        quality_score = data.get("quality_score", 0)

        match_pct = (
            round((matched / total) * 100, 2)
            if total else 0
        )

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

    # ---------------------------------------------------------
    def __build_missing_sheet(
        self,
        workbook,
        data: Dict[str, Any],
    ) -> None:
        bold = workbook.add_format({"bold": True})
        ws = workbook.add_worksheet("Missing Sections")

        ws.write_row(
            0,
            0,
            ["Section ID", "Title", "Page"],
            bold,
        )

        for row, sec in enumerate(
            data.get("missing", []),
            start=1,
        ):
            ws.write_row(
                row,
                0,
                [
                    sec["section_id"],
                    sec["title"],
                    sec["page"],
                ],
            )

    # ---------------------------------------------------------
    def __build_mismatch_sheet(
        self,
        workbook,
        data: Dict[str, Any],
    ) -> None:
        bold = workbook.add_format({"bold": True})
        ws = workbook.add_worksheet("Title Mismatches")

        ws.write_row(
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
            data.get("title_mismatches", []),
            start=1,
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

    # ---------------------------------------------------------
    def __build_page_error_sheet(
        self,
        workbook,
        data: Dict[str, Any],
    ) -> None:
        bold = workbook.add_format({"bold": True})
        ws = workbook.add_worksheet("Page Errors")

        ws.write_row(
            0,
            0,
            [
                "Section ID",
                "TOC Page",
                "Chunk Page Range",
            ],
            bold,
        )

        for row, err in enumerate(
            data.get("page_discrepancies", []),
            start=1,
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
