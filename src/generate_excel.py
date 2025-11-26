#!/usr/bin/env python3
"""
Generate Excel validation report.
Turns JSONL + validator output into XLSX.
"""

import json
import sys
from pathlib import Path
from typing import List

import pandas as pd
import openpyxl.styles


class ExcelReportGenerator:
    """
    Generates a styled Excel report comparing ToC sections
    with parsed content chunks.
    """

    def __init__(
        self,
        toc_path: str,
        chunks_path: str,
        output_xlsx: str
    ):
        """Initialize file paths."""
        self.toc_path = toc_path
        self.chunks_path = chunks_path
        self.output_xlsx = output_xlsx
        self.merged = None

        self.color_map = {
            "MATCHED": "c6efce",
            "MISSING_IN_CONTENT": "ffc7ce",
            "EXTRA_IN_CONTENT": "ffeb9c",
        }

    # --------------------------
    #       DATA LOADING
    # --------------------------

    @staticmethod
    def load_jsonl(path: str) -> List[dict]:
        """Load JSONL file into list of dictionaries."""
        items = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    items.append(json.loads(line))
        return items

    @staticmethod
    def create_toc_dataframe(toc: List[dict]) -> pd.DataFrame:
        """Return DataFrame with selected ToC columns."""
        cols = ["section_id", "title", "page", "level", "full_path"]
        return pd.DataFrame(toc)[cols]

    @staticmethod
    def create_chunk_dataframe(chunks: List[dict]) -> pd.DataFrame:
        """Return DataFrame with selected chunk columns."""
        cols = ["section_id", "start_heading", "start_page", "end_page"]
        return pd.DataFrame(chunks)[cols]

    # --------------------------
    #        MERGING LOGIC
    # --------------------------

    def merge_dataframes(
        self,
        toc_df: pd.DataFrame,
        chunk_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Merge ToC and chunk DataFrames with match status."""
        merged = toc_df.merge(
            chunk_df,
            on="section_id",
            how="outer",
            indicator=True,
        )
        merged["_merge"] = merged["_merge"].map(
            {
                "both": "MATCHED",
                "left_only": "MISSING_IN_CONTENT",
                "right_only": "EXTRA_IN_CONTENT",
            }
        )
        return merged

    # --------------------------
    #      EXCEL GENERATION
    # --------------------------

    def generate(self) -> None:
        """Generate Excel file and print summary."""
        toc = self.load_jsonl(self.toc_path)
        chunks = self.load_jsonl(self.chunks_path)

        toc_df = self.create_toc_dataframe(toc)
        chunk_df = self.create_chunk_dataframe(chunks)

        self.merged = self.merge_dataframes(toc_df, chunk_df)

        with pd.ExcelWriter(
            self.output_xlsx,
            engine="openpyxl"
        ) as writer:
            self.merged.to_excel(
                writer,
                sheet_name="ToC_vs_Content",
                index=False
            )
            self._apply_styles(writer)

        self._print_summary()

    def _apply_styles(self, writer) -> None:
        """Apply color styling based on merge status."""
        sheet = writer.sheets["ToC_vs_Content"]
        merge_col = self.merged.columns.get_loc("_merge")
        last_row = len(self.merged) + 1

        for row in sheet.iter_rows(min_row=2, max_row=last_row):
            status_cell = row[merge_col]
            status = status_cell.value

            fill = openpyxl.styles.PatternFill(
                start_color=self.color_map.get(status, "ffffff"),
                fill_type="solid",
            )

            for cell in row:
                cell.fill = fill

    # --------------------------
    #       SUMMARY OUTPUT
    # --------------------------

    def _print_summary(self) -> None:
        """Print summary of the Excel report."""
        path = Path(self.output_xlsx).resolve()

        total = len(self.merged)
        matched = (self.merged["_merge"] == "MATCHED").sum()
        missing = (
            self.merged["_merge"] == "MISSING_IN_CONTENT"
        ).sum()
        extra = (
            self.merged["_merge"] == "EXTRA_IN_CONTENT"
        ).sum()

        print(f"Excel report generated: {path}")
        print(f"Total sections: {total}")
        print(f"Matched: {matched}")
        print(f"Missing: {missing}")
        print(f"Extra: {extra}")


# ------------------------------
#            MAIN
# ------------------------------

def main(toc_path: str, chunks_path: str, output_xlsx: str):
    """Run Excel report generator."""
    generator = ExcelReportGenerator(
        toc_path,
        chunks_path,
        output_xlsx
    )
    generator.generate()


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(
            "Usage: python generate_excel.py "
            "toc.jsonl content.jsonl report.xlsx"
        )
        sys.exit(1)

    main(sys.argv[1], sys.argv[2], sys.argv[3])
