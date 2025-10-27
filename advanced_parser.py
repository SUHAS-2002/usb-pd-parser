import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict
import pdfplumber
import json

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
    
    HEADING_PATTERN = r'^(\d+(?:\.\d+)*)\s+([A-Z].*?)$'
    FIGURE_PATTERN = r'Figure\s+(\d+[-\.\d]*):?\s*(.*?)(?=\n|$)'
    TABLE_PATTERN = r'Table\s+(\d+[-\.\d]*):?\s*(.*?)(?=\n|$)'
    
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.chunks: List[ContentChunk] = []
    
    def extract_full_document(self, start_page: int = 0, end_page: Optional[int] = None) -> Dict[int, str]:
        """Extract all text from PDF by page."""
        logger.info(f"Extracting full document from {self.pdf_path}")
        pages_text = {}
        
        with pdfplumber.open(self.pdf_path) as pdf:
            end = end_page or len(pdf.pages)
            for i, page in enumerate(pdf.pages[start_page:end], start=start_page):
                text = page.extract_text()
                if text:
                    pages_text[i + 1] = text
        
        logger.info(f"Extracted {len(pages_text)} pages")
        return pages_text
    
    def detect_headings(self, text: str) -> List[Dict[str, any]]:
        """Detect section headings in text."""
        headings = []
        lines = text.split('\n')
        
        for line_num, line in enumerate(lines):
            match = re.match(self.HEADING_PATTERN, line.strip())
            if match:
                section_id = match.group(1)
                title = match.group(2).strip()
                level = len(section_id.split('.'))
                
                headings.append({
                    'section_id': section_id,
                    'title': title,
                    'level': level,
                    'line_num': line_num,
                    'full_path': f"{section_id} {title}"
                })
        
        return headings
    
    def extract_figures_and_tables(self, text: str) -> Tuple[List[str], List[str]]:
        """Extract figure and table references from text."""
        figures = re.findall(self.FIGURE_PATTERN, text, re.MULTILINE)
        tables = re.findall(self.TABLE_PATTERN, text, re.MULTILINE)
        
        figure_list = [f"Figure {fig[0]}" + (f": {fig[1]}" if fig[1] else "") for fig in figures]
        table_list = [f"Table {tbl[0]}" + (f": {tbl[1]}" if tbl[1] else "") for tbl in tables]
        
        return figure_list, table_list
    
    def chunk_by_headings(self, pages_text: Dict[int, str]) -> List[ContentChunk]:
        """Create logical chunks based on section headings."""
        chunks = []
        current_chunk = None
        current_content = []
        current_pages = []
        
        for page_num, text in sorted(pages_text.items()):
            lines = text.split('\n')
            headings = self.detect_headings(text)
            
            for heading in headings:
                # Save previous chunk
                if current_chunk:
                    content = '\n'.join(current_content)
                    figures, tables = self.extract_figures_and_tables(content)
                    
                    chunk = ContentChunk(
                        section_path=current_chunk['full_path'],
                        start_heading=current_chunk['full_path'],
                        content=content,
                        tables=tables,
                        figures=figures,
                        page_range=(min(current_pages), max(current_pages)),
                        section_id=current_chunk['section_id'],
                        level=current_chunk['level']
                    )
                    chunks.append(chunk)
                
                # Start new chunk
                current_chunk = heading
                current_content = []
                current_pages = [page_num]
            
            # Add content to current chunk
            if current_chunk:
                current_content.append(text)
                if page_num not in current_pages:
                    current_pages.append(page_num)
        
        # Save last chunk
        if current_chunk and current_content:
            content = '\n'.join(current_content)
            figures, tables = self.extract_figures_and_tables(content)
            
            chunk = ContentChunk(
                section_path=current_chunk['full_path'],
                start_heading=current_chunk['full_path'],
                content=content,
                tables=tables,
                figures=figures,
                page_range=(min(current_pages), max(current_pages)),
                section_id=current_chunk['section_id'],
                level=current_chunk['level']
            )
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} content chunks")
        return chunks
    
    def save_chunks_to_jsonl(self, output_path: str):
        """Save chunks to JSONL format."""
        with open(output_path, 'w', encoding='utf-8') as f:
            for chunk in self.chunks:
                f.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + '\n')
        logger.info(f"Saved {len(self.chunks)} chunks to {output_path}")
    
    def run(self, output_path: str = "chunks.jsonl", start_page: int = 10):
        """Run advanced parsing pipeline."""
        pages_text = self.extract_full_document(start_page=start_page)
        self.chunks = self.chunk_by_headings(pages_text)
        self.save_chunks_to_jsonl(output_path)
        return self.chunks