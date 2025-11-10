#!/usr/bin/env python3
"""
Generate Excel validation
Turns JSONL + validator output into XLSX
"""

import json
import pandas as pd
from pathlib import Path
from typing import List
import sys
import openpyxl.styles

class ExcelReportGenerator:
    """Generates and styles Excel report from ToC and content JSONL data."""
    
    def __init__(self, toc_path: str, chunks_path: str, output_xlsx: str):
        """Initialize with file paths."""
        self.toc_path = toc_path
        self.chunks_path = chunks_path
        self.output_xlsx = output_xlsx
        self.merged = None
        self.color_map = {
            'MATCHED': 'c6efce',
            'MISSING_IN_CONTENT': 'ffc7ce',
            'EXTRA_IN_CONTENT': 'ffeb9c'
        }

    @staticmethod
    def load_jsonl(path: str) -> List[dict]:
        """Load JSONL file into a list of dictionaries."""
        data = []
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data

    @staticmethod
    def create_toc_dataframe(toc: List[dict]) -> pd.DataFrame:
        """Create DataFrame for ToC data with selected columns."""
        columns = ['section_id', 'title', 'page', 'level', 'full_path']
        return pd.DataFrame(toc)[columns]

    @staticmethod
    def create_chunk_dataframe(chunks: List[dict]) -> pd.DataFrame:
        """Create DataFrame for chunk data with selected columns."""
        columns = ['section_id', 'start_heading', 'start_page', 'end_page']
        return pd.DataFrame(chunks)[columns]

    def merge_dataframes(self, toc_df: pd.DataFrame, chunk_df: pd.DataFrame) -> pd.DataFrame:
        """Merge ToC and chunk DataFrames with status mapping."""
        merged = toc_df.merge(
            chunk_df,
            on='section_id',
            how='outer',
            indicator=True
        )
        merged['_merge'] = merged['_merge'].map({
            'both': 'MATCHED',
            'left_only': 'MISSING_IN_CONTENT',
            'right_only': 'EXTRA_IN_CONTENT'
        })
        return merged

    def generate(self):
        """Generate and save styled Excel report."""
        # Load and prepare data
        toc = self.load_jsonl(self.toc_path)
        chunks = self.load_jsonl(self.chunks_path)
        toc_df = self.create_toc_dataframe(toc)
        chunk_df = self.create_chunk_dataframe(chunks)
        self.merged = self.merge_dataframes(toc_df, chunk_df)

        # Write to Excel with styling
        with pd.ExcelWriter(self.output_xlsx, engine='openpyxl') as writer:
            self.merged.to_excel(writer, sheet_name='ToC_vs_Content', index=False)
            self._apply_styles(writer)

        # Print summary
        self._print_summary()

    def _apply_styles(self, writer):
        """Apply color styling to Excel worksheet based on merge status."""
        worksheet = writer.sheets['ToC_vs_Content']
        for row in worksheet.iter_rows(min_row=2, max_row=len(self.merged) + 1):
            status_cell = row[self.merged.columns.get_loc('_merge')]
            status_cell.style = 'Pandas'
            fill = openpyxl.styles.PatternFill(
                start_color=self.color_map[status_cell.value],
                fill_type='solid'
            )
            for cell in row:
                cell.fill = pd.io.formats.excel.Fill.from_openpyxl(fill)

    def _print_summary(self):
        """Print summary of the generated report."""
        output_path = Path(self.output_xlsx).resolve()
        total = len(self.merged)
        matched = len(self.merged[self.merged['_merge'] == 'MATCHED'])
        missing = len(self.merged[self.merged['_merge'] == 'MISSING_IN_CONTENT'])
        extra = len(self.merged[self.merged['_merge'] == 'EXTRA_IN_CONTENT'])

        print(f"   Excel report generated: {output_path}")
        print(f"   {total} total sections")
        print(f"   {matched} matched")
        print(f"   {missing} missing")
        print(f"   {extra} extra")

def main(toc_path: str, chunks_path: str, output_xlsx: str):
    """Run the Excel report generation."""
    generator = ExcelReportGenerator(toc_path, chunks_path, output_xlsx)
    generator.generate()

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python generate_excel.py toc.jsonl content.jsonl report.xlsx")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])