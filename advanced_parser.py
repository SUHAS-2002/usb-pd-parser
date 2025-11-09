import json
import logging
import re
from dataclasses import asdict, dataclass
from pathlib import Path
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

    def to_dict(self):
        return asdict(self)


class HeadingDetector:
    """Detects section headings in page text."""
    PATTERN = re.compile(
        r"^(\d+(?:\.\d+))\s+([A-Z].?)$", re.MULTILINE
    )

    @staticmethod
    def find_in_page(text: str, page_num: int) -> List[Dict]:
        """Find all headings on a page."""
        headings = []
        for match in HeadingDetector.PATTERN.finditer(text):
            section_id = match.group(1).strip()
            title = match.group(2).strip()
            level = len(section_id.split("."))
            line_offset = text.count("\n", 0, match.start())

            headings.append({
                "section_id": section_id,
                "title": title,
                "level": level,
                "page_num": page_num,
                "line_offset": line_offset,
                "full_path": f"{section_id} {title}",
            })
        return headings


class MediaExtractor:
    """Extracts figure and table captions."""
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
        """Extract figures and tables from text block."""
        figures = [
            f"Figure {m.group(1)}" + (f": {m.group(2)}" if m.group(2).strip() else "")
            for m in cls.FIGURE_PAT.finditer(text)
        ]
        tables = [
            f"Table {m.group(1)}" + (f": {m.group(2)}" if m.group(2).strip() else "")
            for m in cls.TABLE_PAT.finditer(text)
        ]
        return figures, tables


class PageTextCache:
    """Caches extracted page text."""
    def __init__(self):
        self.text_by_page: Dict[int, str] = {}

    def extract(
        self,
        pdf_path: Path,
        start_page: int = 0,
        end_page: Optional[int] = None,
    ) -> None:
        """Fill cache with page text."""
        self.text_by_page.clear()
        with pdfplumber.open(pdf_path) as pdf:
            end = end_page or len(pdf.pages)
            pages = pdf.pages[start_page:end]
            for page in pages:
                text = page.extract_text()
                if text:
                    self.text_by_page[page.page_number] = text
        logger.info(f"Extracted {len(self.text_by_page)} pages")


class ChunkBuilder:
    """Builds ContentChunk objects from headings and text."""
    def __init__(self):
        self.chunks: List[ContentChunk] = []

    def build(
        self,
        page_texts: Dict[int, str],
        all_headings: List[Dict],
    ) -> List[ContentChunk]:
        """Main chunking logic - now < 40 lines."""
        self.chunks = []
        current = None
        buffer_lines = []
        buffer_pages = []

        # Sort headings by appearance order
        headings_sorted = sorted(
            all_headings, key=lambda h: (h["page_num"], h["line_offset"])
        )

        heading_map = {
            (h["page_num"], h["line_offset"]): h for h in headings_sorted
        }

        for page_num, text in sorted(page_texts.items()):
            lines = text.split("\n")
            for line_idx, line in enumerate(lines):
                key = (page_num, line_idx)
                if key in heading_map:
                    self._flush_current(
                        current, buffer_lines, buffer_pages
                    )
                    current = heading_map[key]
                    buffer_lines = [line]
                    buffer_pages = [page_num]
                else:
                    if current:
                        buffer_lines.append(line)
                        if page_num not in buffer_pages:
                            buffer_pages.append(page_num)

        self._flush_current(current, buffer_lines, buffer_pages)
        logger.info(f"Built {len(self.chunks)} chunks")
        return self.chunks

    def _flush_current(
        self,
        current: Optional[Dict],
        lines: List[str],
        pages: List[int],
    ) -> None:
        """Save current buffer as chunk."""
        if not current or not lines:
            return

        content = "\n".join(lines).strip()
        figures, tables = MediaExtractor.extract(content)

        chunk = ContentChunk(
            section_path=current["full_path"],
            start_heading=current["full_path"],
            content=content,
            tables=tables,
            figures=figures,
            page_range=(min(pages), max(pages)),
            section_id=current["section_id"],
            level=current["level"],
        )
        self.chunks.append(chunk)


class AdvancedUSBPDParser:
    """Main parser orchestrating all components."""
    def __init__(self, pdf_path: str):
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
        """Execute full parsing pipeline."""
        logger.info(f"Parsing {self.pdf_path.name}")
        self.cache.extract(self.pdf_path, start_page=start_page)

        # Detect all headings
        all_headings = []
        for page_num, text in self.cache.text_by_page.items():
            headings = HeadingDetector.find_in_page(text, page_num)
            all_headings.extend(headings)

        # Build chunks
        self.chunks = self.builder.build(
            self.cache.text_by_page, all_headings
        )

        # Save
        self._save(output_path)
        logger.info(f"Success! {len(self.chunks)} chunks → {output_path}")
        return self.chunks

    def _save(self, output_path: str) -> None:
        """Save chunks to JSONL."""
        path = Path(output_path)
        with path.open("w", encoding="utf-8") as f:
            for chunk in self.chunks:
                json.dump(chunk.to_dict(), f, ensure_ascii=False)
                f.write("\n")
        logger.info(f"Saved to {path.resolve()}")


# === USAGE ===
if __name__ == "__main__":
    parser = AdvancedUSBPDParser("usb_pd_spec.pdf")
    chunks = parser.run("usb_pd_chunks.jsonl", start_page=15)