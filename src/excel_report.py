from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font
from openpyxl.utils import get_column_letter
from openpyxl.chart import BarChart, Reference

from src.core.base_report_generator import BaseReportGenerator
from src.utils.jsonl_utils import JSONLHandler
from src.config import CONFIG


class ExcelReportGenerator(BaseReportGenerator):
    """
    Excel coverage report generator.

    Implements the BaseReportGenerator template method
    and supports context manager usage.
    """

    # ------------------------------------------------------------------
    def __init__(
        self,
        toc_path: str,
        chunks_path: str,
        output_xlsx: str,
    ) -> None:
        super().__init__(output_xlsx)

        self._toc_path = Path(toc_path)
        self._chunks_path = Path(chunks_path)

        self._colors = {
            "MATCHED": CONFIG.excel_colors.GREEN,
            "MISSING_IN_CONTENT": CONFIG.excel_colors.RED,
            "EXTRA_IN_CONTENT": CONFIG.excel_colors.YELLOW,
        }

    # ------------------------------------------------------------------
    # Special methods (Improvement 10)
    # ------------------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable description."""
        return (
            "ExcelReportGenerator("
            f"toc={self._toc_path.name}, "
            f"chunks={self._chunks_path.name}"
            ")"
        )

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            "ExcelReportGenerator("
            f"toc_path={self._toc_path!r}, "
            f"chunks_path={self._chunks_path!r}, "
            f"output_path={self.output_path!r}"
            ")"
        )

    def __eq__(self, other: object) -> bool:
        """Logical equality based on input sources."""
        if not isinstance(other, ExcelReportGenerator):
            return NotImplemented
        return (
            self._toc_path == other._toc_path
            and self._chunks_path == other._chunks_path
            and self.output_path == other.output_path
        )

    def __len__(self) -> int:
        """Number of input sources."""
        return 2

    # ------------------------------------------------------------------
    # Context Manager Support (Improvement 9)
    # ------------------------------------------------------------------
    def __enter__(self) -> "ExcelReportGenerator":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False

    def __del__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Template method steps
    # ------------------------------------------------------------------
    def _validate_inputs(self) -> None:
        if not self._toc_path.exists():
            raise FileNotFoundError(
                f"ToC file not found: {self._toc_path}"
            )
        if not self._chunks_path.exists():
            raise FileNotFoundError(
                f"Chunks file not found: {self._chunks_path}"
            )

    def _load_data(self) -> Dict[str, Any]:
        return {
            "toc": JSONLHandler.load(self._toc_path),
            "chunks": JSONLHandler.load(self._chunks_path),
        }

    def _process_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        toc_map = self._safe_map(data["toc"])
        chunk_map = self._safe_map(data["chunks"])

        all_ids = sorted(
            set(toc_map) | set(chunk_map),
            key=self._sort_key,
        )

        rows: List[Dict[str, Any]] = []

        for sid in all_ids:
            t = toc_map.get(sid)
            c = chunk_map.get(sid)

            rows.append(
                {
                    "section_id": sid,
                    "toc_title": t["title"] if t else None,
                    "toc_page": t["page"] if t else None,
                    "chunk_title": c["title"] if c else None,
                    "chunk_page": c["page"] if c else None,
                    "status": self._resolve_status(t, c),
                }
            )

        return {"rows": rows}

    def _format_output(self, data: Dict[str, Any]) -> pd.DataFrame:
        return pd.DataFrame(data["rows"])

    def _save_report(self, df: pd.DataFrame) -> Path:
        final_output = self._timestamped_filename(
            self.output_path.stem,
            self.output_path.suffix,
        )

        df.to_excel(final_output, index=False, sheet_name="coverage")

        wb = load_workbook(final_output)
        ws = wb["coverage"]

        self._apply_row_colors(ws)
        self._apply_sheet_formatting(ws)
        self._add_summary_sheet(wb, df)

        wb.save(final_output)
        return final_output

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_status(toc, chunk) -> str:
        if toc and chunk:
            return "MATCHED"
        if toc:
            return "MISSING_IN_CONTENT"
        return "EXTRA_IN_CONTENT"

    @staticmethod
    def _safe_map(
        data: List[Dict[str, Any]]
    ) -> Dict[str, Dict[str, Any]]:
        return {
            d["section_id"]: d
            for d in data
            if isinstance(d, dict) and "section_id" in d
        }

    @staticmethod
    def _sort_key(section_id: Any) -> List[int]:
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

    # ------------------------------------------------------------------
    # Excel formatting
    # ------------------------------------------------------------------
    def _apply_row_colors(self, ws) -> None:
        for row in ws.iter_rows(min_row=2):
            status = row[5].value
            color = self._colors.get(
                status,
                CONFIG.excel_colors.WHITE,
            )
            fill = PatternFill(
                start_color=color,
                end_color=color,
                fill_type="solid",
            )
            for cell in row:
                cell.fill = fill

    @staticmethod
    def _apply_sheet_formatting(ws) -> None:
        ws.auto_filter.ref = "A1:F1"
        ws.freeze_panes = "A2"

        for col in ws.columns:
            values = [
                str(cell.value)
                for cell in col
                if cell.value is not None
            ]
            width = max((len(v) for v in values), default=8)
            col_letter = get_column_letter(col[0].column)
            ws.column_dimensions[col_letter].width = width + 2

        for row in ws.iter_rows(min_row=2):
            cell = row[0]
            cell.hyperlink = f"#coverage!A{cell.row}"
            cell.style = "Hyperlink"

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    @staticmethod
    def _add_summary_sheet(wb, df: pd.DataFrame) -> None:
        summary = wb.create_sheet("summary")

        total = len(df)
        matched = int((df["status"] == "MATCHED").sum())
        missing = int((df["status"] == "MISSING_IN_CONTENT").sum())
        extra = int((df["status"] == "EXTRA_IN_CONTENT").sum())
        match_pct = round((matched / total) * 100, 2) if total else 0

        rows = [
            ["Metric", "Value"],
            ["Total Sections", total],
            ["Matched", matched],
            ["Missing", missing],
            ["Extra", extra],
            ["Match %", match_pct],
        ]

        for r in rows:
            summary.append(r)

        for cell in summary[1]:
            cell.font = Font(bold=True)

        chart = BarChart()
        chart.title = "Content Match Summary"

        data_ref = Reference(summary, min_col=2, min_row=3, max_row=5)
        label_ref = Reference(summary, min_col=1, min_row=3, max_row=5)

        chart.add_data(data_ref, titles_from_data=False)
        chart.set_categories(label_ref)

        summary.add_chart(chart, "D2")
