# src/excel_report.py

import json
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference


class ExcelReportGenerator:
    """
    Generates Excel coverage report:
      - Coverage sheet with colors
      - Summary sheet + chart
      - Auto-fit columns, filters, freeze panes
    """

    GREEN = "C6EFCE"
    RED = "FFC7CE"
    YELLOW = "FFEB9C"

    def __init__(
        self,
        toc_path: str,
        chunks_path: str,
        output_xlsx: str,
    ) -> None:

        self.toc_path = Path(toc_path)
        self.chunks_path = Path(chunks_path)
        self.output_xlsx = Path(output_xlsx)

    # ------------------------------------------------------------------
    @staticmethod
    def _load_jsonl(path: Path) -> List[Dict]:
        """Load JSONL into a list of dictionaries."""
        items: List[Dict] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    items.append(json.loads(line))
        return items

    # ------------------------------------------------------------------
    def _timestamped_output(self) -> Path:
        """Create timestamped output filename."""
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"{self.output_xlsx.stem}_{stamp}{self.output_xlsx.suffix}"
        return self.output_xlsx.parent / name

    # ------------------------------------------------------------------
    def _safe_map(self, data: List[Dict]) -> Dict[str, Dict]:
        """Safely create map: section_id → entry."""
        return {
            d["section_id"]: d
            for d in data
            if isinstance(d, dict) and "section_id" in d
        }

    # ------------------------------------------------------------------
    @staticmethod
    def _sort_key(section_id: Any) -> List[int]:
        """
        Stable sort key for section IDs.

        Order:
          - Front matter: FM-0, FM-1, ...
          - Numeric: 1, 1.1, 2.3.4
        """
        if section_id is None:
            return [9999]

        sid = str(section_id)

        # Front-matter sections
        if sid.startswith("FM-"):
            try:
                return [-1, int(sid.split("-")[1])]
            except Exception:
                return [-1, 0]

        # Numeric sections
        try:
            return [int(x) for x in sid.split(".")]
        except Exception:
            return [9999]

    # ------------------------------------------------------------------
    def generate(self) -> Path:
        """Generate full Excel coverage report."""
        toc = self._load_jsonl(self.toc_path)
        chunks = self._load_jsonl(self.chunks_path)

        toc_map = self._safe_map(toc)
        chunk_map = self._safe_map(chunks)

        all_ids = sorted(
            set(toc_map) | set(chunk_map),
            key=self._sort_key,
        )

        rows: List[Dict] = []

        # ----------------- Build coverage table -------------------------
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
                    "chunk_title": c["title"] if c else None,
                    "chunk_page": c["page"] if c else None,
                    "status": status,
                }
            )

        df = pd.DataFrame(rows)

        final_output = self._timestamped_output()
        df.to_excel(final_output, index=False, sheet_name="coverage")

        wb = load_workbook(final_output)
        ws = wb["coverage"]

        # -------------------- Row Coloring -----------------------------
        colors = {
            "MATCHED": self.GREEN,
            "MISSING_IN_CONTENT": self.RED,
            "EXTRA_IN_CONTENT": self.YELLOW,
        }

        for row in ws.iter_rows(min_row=2):
            status = row[5].value
            color = colors.get(status, "FFFFFF")
            fill = PatternFill(
                start_color=color,
                end_color=color,
                fill_type="solid",
            )
            for cell in row:
                cell.fill = fill

        # ---------------- Hyperlinks ----------------------------------
        for row in ws.iter_rows(min_row=2):
            cell = row[0]
            cell.hyperlink = f"#coverage!A{cell.row}"
            cell.style = "Hyperlink"

        # ---------------- Filters + Freeze header ----------------------
        ws.auto_filter.ref = "A1:F1"
        ws.freeze_panes = "A2"

        # ---------------- Auto-fit columns -----------------------------
        for col in ws.columns:
            values = [
                str(cell.value)
                for cell in col
                if cell.value is not None
            ]
            width = max((len(v) for v in values), default=8)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = width + 2

        # ---------------- Summary sheet --------------------------------
        summary = wb.create_sheet("summary")

        total = len(df)
        matched = (df["status"] == "MATCHED").sum()
        missing = (df["status"] == "MISSING_IN_CONTENT").sum()
        extra = (df["status"] == "EXTRA_IN_CONTENT").sum()

        match_pct = round((matched / total) * 100, 2) if total else 0

        summary_rows = [
            ["Metric", "Value"],
            ["Total Sections", total],
            ["Matched", matched],
            ["Missing", missing],
            ["Extra", extra],
            ["Match %", match_pct],
        ]

        for row in summary_rows:
            summary.append(row)

        for cell in summary[1]:
            cell.font = Font(bold=True)

        # ---------------- Chart ---------------------------------------
        chart = BarChart()
        chart.title = "Content Match Summary"

        data_ref = Reference(summary, min_col=2, min_row=3, max_row=5)
        label_ref = Reference(summary, min_col=1, min_row=3, max_row=5)

        chart.add_data(data_ref, titles_from_data=False)
        chart.set_categories(label_ref)

        summary.add_chart(chart, "D2")

        wb.save(final_output)

        print(f"\n✔ Excel report generated → {final_output}\n")
        return final_output
