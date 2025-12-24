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
    Generates Excel coverage report.

    Encapsulation rules:
    - generate() is the ONLY public method
    - filesystem paths are private
    - rendering steps are isolated
    """

    # -------------------- Private constants -------------------
    __GREEN = "C6EFCE"
    __RED = "FFC7CE"
    __YELLOW = "FFEB9C"

    # ---------------------------------------------------------
    # Construction (private state)
    # ---------------------------------------------------------
    def __init__(
        self,
        toc_path: str,
        chunks_path: str,
        output_xlsx: str,
    ) -> None:
        self.__toc_path = Path(toc_path)
        self.__chunks_path = Path(chunks_path)
        self.__output_xlsx = Path(output_xlsx)

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def generate(self) -> Path:
        toc = self.__load_jsonl(self.__toc_path)
        chunks = self.__load_jsonl(self.__chunks_path)

        rows = self.__build_rows(toc, chunks)
        df = pd.DataFrame(rows)

        output = self.__timestamped_output()
        self.__write_excel(df, output)
        self.__post_process_excel(output, df)

        print(f"\n✔ Excel report generated → {output}\n")
        return output

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------
    def __load_jsonl(self, path: Path) -> List[Dict]:
        items: List[Dict] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    items.append(json.loads(line))
        return items

    # ---------------------------------------------------------
    def __timestamped_output(self) -> Path:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"{self.__output_xlsx.stem}_{stamp}{self.__output_xlsx.suffix}"
        return self.__output_xlsx.parent / name

    # ---------------------------------------------------------
    def __build_rows(
        self,
        toc: List[Dict],
        chunks: List[Dict],
    ) -> List[Dict]:
        toc_map = self.__safe_map(toc)
        chunk_map = self.__safe_map(chunks)

        all_ids = sorted(
            set(toc_map) | set(chunk_map),
            key=self.__sort_key,
        )

        rows: List[Dict] = []

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

        return rows

    # ---------------------------------------------------------
    def __write_excel(self, df: pd.DataFrame, output: Path) -> None:
        df.to_excel(output, index=False, sheet_name="coverage")

    # ---------------------------------------------------------
    def __post_process_excel(
        self,
        output: Path,
        df: pd.DataFrame,
    ) -> None:
        wb = load_workbook(output)
        ws = wb["coverage"]

        self.__apply_row_colors(ws)
        self.__add_hyperlinks(ws)
        self.__apply_filters(ws)
        self.__auto_fit_columns(ws)
        self.__add_summary_sheet(wb, df)

        wb.save(output)

    # ---------------------------------------------------------
    def __apply_row_colors(self, ws) -> None:
        colors = {
            "MATCHED": self.__GREEN,
            "MISSING_IN_CONTENT": self.__RED,
            "EXTRA_IN_CONTENT": self.__YELLOW,
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

    # ---------------------------------------------------------
    def __add_hyperlinks(self, ws) -> None:
        for row in ws.iter_rows(min_row=2):
            cell = row[0]
            cell.hyperlink = f"#coverage!A{cell.row}"
            cell.style = "Hyperlink"

    # ---------------------------------------------------------
    def __apply_filters(self, ws) -> None:
        ws.auto_filter.ref = "A1:F1"
        ws.freeze_panes = "A2"

    # ---------------------------------------------------------
    def __auto_fit_columns(self, ws) -> None:
        for col in ws.columns:
            values = [
                str(cell.value)
                for cell in col
                if cell.value is not None
            ]
            width = max((len(v) for v in values), default=8)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = width + 2

    # ---------------------------------------------------------
    def __add_summary_sheet(
        self,
        wb,
        df: pd.DataFrame,
    ) -> None:
        summary = wb.create_sheet("summary")

        total = len(df)
        matched = (df["status"] == "MATCHED").sum()
        missing = (df["status"] == "MISSING_IN_CONTENT").sum()
        extra = (df["status"] == "EXTRA_IN_CONTENT").sum()

        match_pct = round(
            (matched / total) * 100, 2
        ) if total else 0

        rows = [
            ["Metric", "Value"],
            ["Total Sections", total],
            ["Matched", matched],
            ["Missing", missing],
            ["Extra", extra],
            ["Match %", match_pct],
        ]

        for row in rows:
            summary.append(row)

        for cell in summary[1]:
            cell.font = Font(bold=True)

        chart = BarChart()
        chart.title = "Content Match Summary"

        data_ref = Reference(
            summary,
            min_col=2,
            min_row=3,
            max_row=5,
        )
        label_ref = Reference(
            summary,
            min_col=1,
            min_row=3,
            max_row=5,
        )

        chart.add_data(data_ref, titles_from_data=False)
        chart.set_categories(label_ref)

        summary.add_chart(chart, "D2")

    # ---------------------------------------------------------
    def __safe_map(self, data: List[Dict]) -> Dict[str, Dict]:
        return {
            d["section_id"]: d
            for d in data
            if isinstance(d, dict) and "section_id" in d
        }

    # ---------------------------------------------------------
    def __sort_key(self, section_id: Any) -> List[int]:
        if section_id is None:
            return [9999]

        sid = str(section_id)

        if sid.startswith("FM-"):
            try:
                return [-1, int(sid.split("-")[1])]
            except Exception:
                return [-1, 0]

        try:
            return [int(x) for x in sid.split(".")]
        except Exception:
            return [9999]
