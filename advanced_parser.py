import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import pdfplumber
import json
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class ContentChunk:
    """Represents a logical chunk of document content."""
    section_path: str
    start_heading: str
    content: str
    tables: List[str]
    figures: List[str]
    page_range: Tuple[int, int]
    section_id: str
    level: int
    
    def to_dict(self):
        return asdict(self)


class AdvancedUSBPDParser:
    """Advanced parser with logical chunking and content extraction."""
    
    HEADING_PATTERN = re.compile(r'^(\d+(?:\.\d+))\s+([A-Z].?)$', re.MULTILINE)
    FIGURE_PATTERN = re.compile(r'Figure\s+(\d+[-\.\d]):?\s(.*?)(?=\n|$)', re.MULTILINE | re.DOTALL)
    TABLE_PATTERN = re.compile(r'Table\s+(\d+[-\.\d]):?\s(.*?)(?=\n|$)', re.MULTILINE | re.DOTALL)
    
    def _init_(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.chunks: List[ContentChunk] = []
        self._pages_text: Dict[int, str] = {}
    
    def run(self, output_path: str = "chunks.jsonl", start_page: int = 10) -> List[ContentChunk]:
        """Run the full parsing pipeline and return chunks."""
        logger.info(f"Starting advanced parsing of {self.pdf_path}")
        self._extract_pages(start_page=start_page)
        self._build_chunks()
        self._save_chunks(output_path)
        logger.info(f"Parsing complete. {len(self.chunks)} chunks generated.")
        return self.chunks

    def _extract_pages(self, start_page: int = 0, end_page: Optional[int] = None) -> None:
        """Extract raw text per page into internal cache."""
        self._pages_text.clear()
        with pdfplumber.open(self.pdf_path) as pdf:
            end = end_page or len(pdf.pages)
            pages = pdf.pages[start_page:end]
            for page in pages:
                text = page.extract_text()
                if text:
                    self._pages_text[page.page_number] = text
        logger.info(f"Extracted text from {len(self._pages_text)} pages")

    def _detect_headings_in_page(self, text: str, page_num: int) -> List[Dict[str, any]]:
        """Detect headings within a single page's text."""
        headings = []
        for match in self.HEADING_PATTERN.finditer(text):
            section_id = match.group(1).strip()
            title = match.group(2).strip()
            level = len(section_id.split('.'))
            line_offset = text.count('\n', 0, match.start())
            
            headings.append({
                'section_id': section_id,
                'title': title,
                'level': level,
                'page_num': page_num,
                'line_offset': line_offset,
                'full_path': f"{section_id} {title}"
            })
        return headings

    def _extract_figures_and_tables(self, text: str) -> Tuple[List[str], List[str]]:
        """Extract formatted figure/table captions from text."""
        figures = [
            f"Figure {m.group(1)}" + (f": {m.group(2)}" if m.group(2).strip() else "")
            for m in self.FIGURE_PATTERN.finditer(text)
        ]
        tables = [
            f"Table {m.group(1)}" + (f": {m.group(2)}" if m.group(2).strip() else "")
            for m in self.TABLE_PATTERN.finditer(text)
        ]
        return figures, tables

    def _build_chunks(self) -> None:
        """Split document into logical ContentChunk objects."""
        self.chunks = []
        current: Optional[Dict[str, any]] = None
        buffer_text: List[str] = []
        buffer_pages: List[int] = []

        all_headings = []
        for page_num, text in sorted(self._pages_text.items()):
            page_headings = self._detect_headings_in_page(text, page_num)
            all_headings.extend(page_headings)

        all_headings.sort(key=lambda h: (h['page_num'], h['line_offset']))

        for page_num, text in sorted(self._pages_text.items()):
            page_headings = [h for h in all_headings if h['page_num'] == page_num]
            heading_idx = 0

            lines = text.split('\n')
            for line_idx, line in enumerate(lines):
                if (heading_idx < len(page_headings) and 
                    page_headings[heading_idx]['line_offset'] == line_idx):
                    
                    if current:
                        content = '\n'.join(buffer_text).strip()
                        figures, tables = self._extract_figures_and_tables(content)
                        self.chunks.append(ContentChunk(
                            section_path=current['full_path'],
                            start_heading=current['full_path'],
                            content=content,
                            tables=tables,
                            figures=figures,
                            page_range=(min(buffer_pages), max(buffer_pages)),
                            section_id=current['section_id'],
                            level=current['level']
                        ))
                    
                    current = page_headings[heading_idx]
                    buffer_text = [line]
                    buffer_pages = [page_num]
                    heading_idx += 1
                else:
                    if current:
                        buffer_text.append(line)
                        if page_num not in buffer_pages:
                            buffer_pages.append(page_num)

        if current and buffer_text:
            content = '\n'.join(buffer_text).strip()
            figures, tables = self._extract_figures_and_tables(content)
            self.chunks.append(ContentChunk(
                section_path=current['full_path'],
                start_heading=current['full_path'],
                content=content,
                tables=tables,
                figures=figures,
                page_range=(min(buffer_pages), max(buffer_pages)),
                section_id=current['section_id'],
                level=current['level']
            ))

        logger.info(f"Built {len(self.chunks)} content chunks")

    def _save_chunks(self, output_path: str) -> None:
        """Write chunks to JSONL file."""
        path = Path(output_path)
        with path.open('w', encoding='utf-8') as f:
            for chunk in self.chunks:
                f.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + '\n')
        logger.info(f"Saved {len(self.chunks)} chunks to {path.resolve()}")