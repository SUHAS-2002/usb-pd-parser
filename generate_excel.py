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

def load_jsonl(path: str) -> List[dict]:
    data = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    return data

def main(toc_path: str, chunks_path: str, output_xlsx: str):
    toc = load_jsonl(toc_path)
    chunks = load_jsonl(chunks_path)
    
    toc_df = pd.DataFrame(toc)[['section_id', 'title', 'page', 'level', 'full_path']]
    chunk_df = pd.DataFrame(chunks)[['section_id', 'start_heading', 'start_page', 'end_page']]
    
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
    
    # Color coding
    def color_status(val):
        color = {'MATCHED': 'background-color: #c6efce',
                 'MISSING_IN_CONTENT': 'background-color: #ffc7ce',
                 'EXTRA_IN_CONTENT': 'background-color: #ffeb9c'}[val]
        return color
    
    with pd.ExcelWriter(output_xlsx, engine='openpyxl') as writer:
        merged.to_excel(writer, sheet_name='ToC_vs_Content', index=False)
        
        workbook = writer.book
        worksheet = writer.sheets['ToC_vs_Content']
        
        # Apply colors
        for row in worksheet.iter_rows(min_row=2, max_row=len(merged)+1):
            status_cell = row[merged.columns.get_loc('_merge')]
            status_cell.style = 'Pandas'
            for cell in row:
                cell.fill = pd.io.formats.excel.Fill.from_openpyxl(
                    openpyxl.styles.PatternFill(
                        start_color=color_status(status_cell.value)[16:-1],
                        fill_type='solid'
                    )
                )
    
    print(f"   Excel report generated: {Path(output_xlsx).resolve()}")
    print(f"   {len(merged)} total sections")
    print(f"   {len(merged[merged['_merge']=='MATCHED'])} matched")
    print(f"   {len(merged[merged['_merge']=='MISSING_IN_CONTENT'])} missing")
    print(f"   {len(merged[merged['_merge']=='EXTRA_IN_CONTENT'])} extra")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python generate_excel.py toc.jsonl content.jsonl report.xlsx")
        sys.exit(1)
    main(sys.argv[1], sys.argv[2], sys.argv[3])