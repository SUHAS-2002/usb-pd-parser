import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference


class ExcelReportGenerator:
    """
    Full Excel report generator with:
    - Colored coverage sheet
    - Summary sheet + chart
    - Auto-fit columns & freeze header
    - Hyperlinks
    - Timestamped output (no overwrite)
    """

    GREEN = "C6EFCE"
    RED = "FFC7CE"
    YELLOW = "FFEB9C"

    def __init__(self, toc_path: str, chunks_path: str, output_xlsx: str):
        self.toc_path = Path(toc_path)
        self.chunks_path = Path(chunks_path)
        self.output_xlsx = Path(output_xlsx)

    @staticmethod
    def _load_jsonl(path: Path) -> List[Dict]:
        data = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data

    def _timestamped_output(self) -> Path:
        """Ensures unique filename to avoid PermissionError."""
        stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        new_name = f"{self.output_xlsx.stem}_{stamp}{self.output_xlsx.suffix}"
        return self.output_xlsx.parent / new_name

    # ---------------------------------------------------------------------
    # MAIN GENERATE FUNCTION
    # ---------------------------------------------------------------------
    def generate(self) -> Path:
        toc = self._load_jsonl(self.toc_path)
        chunks = self._load_jsonl(self.chunks_path)

        toc_map = {e["section_id"]: e for e in toc}
        chunk_map = {c["section_id"]: c for c in chunks}

        all_ids = sorted(set(toc_map) | set(chunk_map))

        rows = []
        for sid in all_ids:
            t = toc_map.get(sid)
            c = chunk_map.get(sid)

            if t and c:
                status = "MATCHED"
            elif t and not c:
                status = "MISSING_IN_CONTENT"
            else:
                status = "EXTRA_IN_CONTENT"

            rows.append(
                {
                    "section_id": sid,
                    "toc_title": t["title"] if t else None,
                    "toc_page": t["page"] if t else None,
                    "chunk_title": c.get("title") if c else None,
                    "chunk_page": c.get("page") if c else None,
                    "status": status,
                }
            )

        df = pd.DataFrame(rows)

        # ----- STEP 1: timestamp output -----
        final_output = self._timestamped_output()

        # ----- STEP 2: write basic Excel file -----
        df.to_excel(final_output, index=False, sheet_name="coverage")

        wb = load_workbook(final_output)
        ws = wb["coverage"]

        # ----- STEP 3: row coloring -----
        color_map = {
            "MATCHED": self.GREEN,
            "MISSING_IN_CONTENT": self.RED,
            "EXTRA_IN_CONTENT": self.YELLOW,
        }

        for row in ws.iter_rows(min_row=2):
            status = row[5].value
            color = color_map.get(status, "FFFFFF")
            fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
            for cell in row:
                cell.fill = fill

        # ----- STEP 4: Hyperlinks -----
        for row in ws.iter_rows(min_row=2):
            row[0].hyperlink = f"#coverage!A{row[0].row}"
            row[0].style = "Hyperlink"

        # ----- STEP 5: Filters + Freeze -----
        ws.auto_filter.ref = "A1:F1"
        ws.freeze_panes = "A2"

        # ----- STEP 6: Autofit columns -----
        for col in ws.columns:
            length = max(len(str(cell.value)) for cell in col if cell.value)
            ws.column_dimensions[get_column_letter(col[0].column)].width = length + 2

        # ----- STEP 7: Summary Sheet -----
        summary = wb.create_sheet("summary")

        total = len(df)
        matched = len(df[df["status"] == "MATCHED"])
        missing = len(df[df["status"] == "MISSING_IN_CONTENT"])
        extra = len(df[df["status"] == "EXTRA_IN_CONTENT"])
        pct = round((matched / total) * 100, 2) if total else 0

        summary_rows = [
            ["Metric", "Value"],
            ["Total Sections", total],
            ["Matched", matched],
            ["Missing", missing],
            ["Extra", extra],
            ["Match %", pct],
        ]

        for row in summary_rows:
            summary.append(row)

        for cell in summary[1]:
            cell.font = Font(bold=True)

        # ----- STEP 8: Add Chart -----
        chart = BarChart()
        chart.title = "Content Match Summary"

        data = Reference(summary, min_col=2, min_row=3, max_row=5)
        labels = Reference(summary, min_col=1, min_row=3, max_row=5)
        chart.add_data(data, titles_from_data=False)
        chart.set_categories(labels)

        summary.add_chart(chart, "D2")

        wb.save(final_output)

        print(f"\n✅ Excel report generated: {final_output}\n")
        return final_output
