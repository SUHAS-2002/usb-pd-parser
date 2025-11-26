#!/usr/bin/env python3
"""
Advanced USB PD PDF parser (refactored, OOP, PEP8-friendly).

This module:
- Extracts page text from a PDF
- Detects numbered headings
- Groups following text into logical content chunks
- Extracts figure/table captions
- Writes chunks to a JSONL file
"""
from dataclasses import asdict, dataclass
from pathlib import Path
import json
import logging
import re
from typing import Dict, List, Optional, Tuple

import pdfplumber

logger = logging.getLogger(__name__)


@dataclass
class ContentChunk:
    """Represents a logical section with content and metadata."""
    section_path: str
    start_heading: str
    content: str
    tables: List[str]
    figures: List[str]
    page_range: Tuple[int, int]
    section_id: str
    level: int

    def to_dict(self) -> Dict:
        return asdict(self)


class HeadingDetector:
    """Detects section headings in page text."""
    # Matches: 1 Title OR 1.2 Title OR 2.3.4 Title etc.
    PATTERN = re.compile(
        r"^(\d+(?:\.\d+)*)\s+([A-Z].+)$", re.MULTILINE
    )

    @staticmethod
    def find_in_page(text: str, page_num: int) -> List[Dict]:
        """Find all headings on a page and return structured dicts."""
        headings: List[Dict] = []
        for match in HeadingDetector.PATTERN.finditer(text):
            section_id = match.group(1).strip()
            title = match.group(2).strip()
            level = len(section_id.split("."))
            # Count newline characters up to the match to get line index.
            line_offset = text.count("\n", 0, match.start())

            headings.append(
                {
                    "section_id": section_id,
                    "title": title,
                    "level": level,
                    "page_num": page_num,
                    "line_offset": line_offset,
                    "full_path": f"{section_id} {title}",
                }
            )
        return headings


class MediaExtractor:
    """Extracts figure and table captions from a block of text."""
    FIGURE_PAT = re.compile(
        r"Figure\s+(\d+[-\.\d]*):?\s*(.*?)(?=\n|$)",
        re.MULTILINE | re.DOTALL,
    )
    TABLE_PAT = re.compile(
        r"Table\s+(\d+[-\.\d]*):?\s*(.*?)(?=\n|$)",
        re.MULTILINE | re.DOTALL,
    )

    @classmethod
    def extract(cls, text: str) -> Tuple[List[str], List[str]]:
        """Return (figures, tables) found in text."""
        figures = [cls._format_caption("Figure", m) for m in
                   cls.FIGURE_PAT.finditer(text)]
        tables = [cls._format_caption("Table", m) for m in
                  cls.TABLE_PAT.finditer(text)]
        return figures, tables

    @staticmethod
    def _format_caption(prefix: str, match: re.Match) -> str:
        """Format a figure/table caption into a single string."""
        identifier = match.group(1)
        caption = match.group(2).strip()
        return prefix + " " + identifier + (f": {caption}" if caption else "")


class PageTextCache:
    """Cache extracted text for each page in a PDF file."""
    def __init__(self) -> None:
        self.text_by_page: Dict[int, str] = {}

    def extract(
        self,
        pdf_path: Path,
        start_page: int = 0,
        end_page: Optional[int] = None,
    ) -> None:
        """
        Populate cache with page text.
        
        start_page and end_page behave like slice indices for pdf.pages.
        """
        self.text_by_page.clear()
        with pdfplumber.open(pdf_path) as pdf:
            end = end_page or len(pdf.pages)
            pages = pdf.pages[start_page:end]
            for page in pages:
                text = page.extract_text()
                if text:
                    # pdfplumber.page.page_number is 1-indexed
                    self.text_by_page[page.page_number] = text
        logger.info("Extracted %d pages", len(self.text_by_page))


class ChunkBuilder:
    """
    Stateful builder that goes through pages and headings and builds
    ContentChunk objects.
    """
    def __init__(self) -> None:
        self.chunks: List[ContentChunk] = []
        # Processing state (moved into instance to avoid long param lists)
        self._current: Optional[Dict] = None
        self._buffer_lines: List[str] = []
        self._buffer_pages: List[int] = []

    def build(
        self,
        page_texts: Dict[int, str],
        all_headings: List[Dict],
    ) -> List[ContentChunk]:
        """Main chunking logic with reduced nesting and clear state."""
        self.chunks = []
        self._current = None
        self._buffer_lines = []
        self._buffer_pages = []

        # Create a lookup from (page_num, line_offset) -> heading dict
        heading_map: Dict[Tuple[int, int], Dict] = {
            (h["page_num"], h["line_offset"]): h
            for h in sorted(all_headings, key=lambda h: (h["page_num"],
                                                         h["line_offset"]))
        }

        # Iterate pages in order
        for page_num, text in sorted(page_texts.items()):
            self._process_page(page_num, text, heading_map)

        # Flush remaining buffered chunk
        self._flush_current()
        logger.info("Built %d chunks", len(self.chunks))
        return self.chunks

    def _process_page(
        self,
        page_num: int,
        text: str,
        heading_map: Dict[Tuple[int, int], Dict],
    ) -> None:
        """
        Process a single page's text and update internal buffers.

        This method now uses instance state variables so callers do not
        need to pass buffers or current state.
        """
        lines = text.split("\n")
        for line_idx, line in enumerate(lines):
            key = (page_num, line_idx)
            if key in heading_map:
                # Found a heading: flush previous chunk and start new one
                self._flush_current()
                self._current = heading_map[key]
                # Start buffer with the heading line
                self._buffer_lines = [line]
                self._buffer_pages = [page_num]
            else:
                # Append to current buffer if a heading was previously found
                if self._current:
                    self._buffer_lines.append(line)
                    if page_num not in self._buffer_pages:
                        self._buffer_pages.append(page_num)

    def _flush_current(self) -> None:
        """Save current buffer as a ContentChunk and reset buffers."""
        if not self._current or not self._buffer_lines:
            return

        content = "\n".join(self._buffer_lines).strip()
        figures, tables = MediaExtractor.extract(content)

        # Defensive: ensure pages list is non-empty
        pages = self._buffer_pages or [self._current.get("page_num", 0)]
        page_range = (min(pages), max(pages))

        chunk = ContentChunk(
            section_path=self._current["full_path"],
            start_heading=self._current["full_path"],
            content=content,
            tables=tables,
            figures=figures,
            page_range=page_range,
            section_id=self._current["section_id"],
            level=self._current["level"],
        )
        self.chunks.append(chunk)

        # Reset state
        self._current = None
        self._buffer_lines = []
        self._buffer_pages = []


class AdvancedUSBPDParser:
    """Main parser orchestrating all components."""
    def __init__(self, pdf_path: str) -> None:
        self.pdf_path = Path(pdf_path)
        self.chunks: List[ContentChunk] = []
        self.cache = PageTextCache()
        self.builder = ChunkBuilder()

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

    def run(
        self,
        output_path: str = "chunks.jsonl",
        start_page: int = 10,
    ) -> List[ContentChunk]:
        """Execute full parsing pipeline and write JSONL output."""
        logger.info("Parsing %s", self.pdf_path.name)
        self.cache.extract(self.pdf_path, start_page=start_page)

        # Detect all headings across the cached pages
        all_headings: List[Dict] = []
        for page_num, text in self.cache.text_by_page.items():
            headings = HeadingDetector.find_in_page(text, page_num)
            all_headings.extend(headings)

        # Build content chunks
        self.chunks = self.builder.build(self.cache.text_by_page, all_headings)

        # Persist results
        self._save(output_path)
        logger.info("Success! %d chunks → %s", len(self.chunks), output_path)
        return self.chunks

    def _save(self, output_path: str) -> None:
        """Save chunks to a JSONL file."""
        path = Path(output_path)
        with path.open("w", encoding="utf-8") as f:
            for chunk in self.chunks:
                json.dump(chunk.to_dict(), f, ensure_ascii=False)
                f.write("\n")
        logger.info("Saved to %s", str(path.resolve()))


# === USAGE ===
if __name__ == "__main__":
    # Basic logging to console for convenience when running as script
    logging.basicConfig(level=logging.INFO)
    parser = AdvancedUSBPDParser("usb_pd_spec.pdf")
    parser.run("usb_pd_chunks.jsonl", start_page=15)
