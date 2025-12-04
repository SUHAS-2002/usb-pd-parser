"""
advanced_parser.py
==================
USB Power Delivery Specification - Advanced OOP Parser
Version: 4.0 - Full PDF Coverage + OCR Fallback
"""

from __future__ import annotations
import argparse
import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any

import pdfplumber

try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

# --------------------------
# Logging Setup
# --------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# --------------------------
# Data Classes
# --------------------------
@dataclass
class TocEntry:
    doc_title: str
    section_id: str
    title: str
    full_path: str
    page: int
    level: int
    parent_id: Optional[str]
    tags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContentChunk:
    doc_title: str
    section_id: str
    section_path: str
    start_heading: str
    start_page: int
    end_page: int
    content: str
    subsections: List[str] = field(default_factory=list)
    tables: List[Dict] = field(default_factory=list)
    figures: List[Dict] = field(default_factory=list)
    word_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ParserConfig:
    output_toc: str = "usb_pd_toc.jsonl"
    output_content: str = "usb_pd_content.jsonl"
    extract_content: bool = True
    scan_all_toc: bool = True
    batch_size: int = 50
    use_ocr: bool = False


# --------------------------
# TOC Extraction
# --------------------------
class TocExtractor:
    TOC_PATTERNS = [
        r"^(\d+(?:\.\d+)*)\s+([^\.\d][^\n]+?)\s*\.{2,}\s*(\d+)\s*$",
        r"^(\d+(?:\.\d+)*)\s+([^\.\d][^\n]+?)\s{3,}(\d+)\s*$",
    ]

    def __init__(self, parser: USBPDParser):
        self.parser = parser

    def extract_toc_text(self, scan_all: bool = True) -> Tuple[str, List[int]]:
        toc_text = ""
        toc_pages: List[int] = []
        try:
            with pdfplumber.open(self.parser.pdf_path) as pdf:
                total_pages = len(pdf.pages)
                max_scan = total_pages if scan_all else min(50, total_pages)

                for i in range(max_scan):
                    page = pdf.pages[i]
                    text = page.extract_text() or ""
                    if "contents" in text.lower() or re.search(r"^\d+(\.\d+)*\s+", text, re.MULTILINE):
                        toc_text += text + "\n"
                        toc_pages.append(i + 1)
        except Exception as e:
            logger.error(f"TOC extraction error: {e}")
            raise
        return toc_text, toc_pages

    def parse_toc_line(self, line: str) -> Optional[Dict[str, Any]]:
        line = line.strip()
        if not line or len(line) < 5:
            return None
        for pattern in self.TOC_PATTERNS:
            match = re.match(pattern, line)
            if match:
                section_id, title, page = match.groups()
                title = re.sub(r"\.{2,}", "", title).strip()
                try:
                    page_num = int(page)
                    if not (1 <= page_num <= 10000):
                        continue
                except ValueError:
                    continue
                return {"section_id": section_id, "title": title, "page": page_num}
        return None

    def parse_toc(self, toc_text: str) -> List[TocEntry]:
        entries: List[TocEntry] = []
        seen = set()
        for line in toc_text.split("\n"):
            parsed = self.parse_toc_line(line)
            if parsed and parsed["section_id"] not in seen:
                seen.add(parsed["section_id"])
                entry = TocEntry(
                    doc_title=self.parser.doc_title,
                    section_id=parsed["section_id"],
                    title=parsed["title"],
                    full_path=self.parser.build_full_path(parsed["section_id"], parsed["title"]),
                    page=parsed["page"],
                    level=self.parser.calculate_level(parsed["section_id"]),
                    parent_id=self.parser.get_parent_id(parsed["section_id"]),
                    tags=self.parser.generate_tags(parsed["title"]),
                )
                entries.append(entry)
        entries.sort(key=lambda x: [int(p) for p in x.section_id.split(".")])
        return entries


# --------------------------
# Content Extraction
# --------------------------
@dataclass
class SectionContext:
    pdf: pdfplumber.pdf.PDF
    entry: TocEntry
    boundaries: Dict[str, Tuple[int, int]]
    batch_size: int
    idx: int


class ContentExtractor:
    def __init__(self, parser: USBPDParser):
        self.parser = parser

    def extract_full_content(self, batch_size: int = 50, use_ocr: bool = False) -> None:
        if not self.parser.toc_entries:
            logger.warning("No TOC entries found; skipping content extraction.")
            return

        with pdfplumber.open(self.parser.pdf_path) as pdf:
            boundaries = self.build_boundaries()
            for idx, entry in enumerate(self.parser.toc_entries, 1):
                ctx = SectionContext(pdf, entry, boundaries, batch_size, idx)
                self.extract_section(ctx, use_ocr)
            self.extract_unmapped_pages(pdf, batch_size, use_ocr)

    def build_boundaries(self) -> Dict[str, Tuple[int, int]]:
        boundaries: Dict[str, Tuple[int, int]] = {}
        sorted_entries = sorted(self.parser.toc_entries, key=lambda e: e.page)
        total_pages = self.parser.total_pdf_pages
        for i, entry in enumerate(sorted_entries):
            start_page = entry.page
            end_page = total_pages
            for next_entry in sorted_entries[i + 1:]:
                if next_entry.level <= entry.level:
                    end_page = next_entry.page - 1
                    break
            boundaries[entry.section_id] = (start_page, min(end_page, total_pages))
        return boundaries

    def extract_section(self, ctx: SectionContext, use_ocr: bool) -> None:
        start_pg, end_pg = ctx.boundaries.get(ctx.entry.section_id, (ctx.entry.page, ctx.entry.page))
        content = self.extract_text(ctx.pdf, start_pg, end_pg, ctx.batch_size, use_ocr)
        if not content.strip():
            return
        chunk = ContentChunk(
            doc_title=self.parser.doc_title,
            section_id=ctx.entry.section_id,
            section_path=ctx.entry.full_path,
            start_heading=ctx.entry.title,
            start_page=start_pg,
            end_page=end_pg,
            content=content,
            subsections=self.parser.find_subsections(ctx.entry.section_id),
            word_count=len(content.split()),
        )
        self.parser.content_chunks.append(chunk)

    def extract_text(self, pdf, start_page, end_page, batch_size, use_ocr) -> str:
        parts: List[str] = []
        for batch_start in range(start_page - 1, end_page, batch_size):
            batch_end = min(batch_start + batch_size, end_page)
            for page_num in range(batch_start, batch_end):
                if page_num >= len(pdf.pages):
                    continue
                page = pdf.pages[page_num]
                text = page.extract_text() or ""
                if not text.strip() and use_ocr and OCR_AVAILABLE:
                    image = page.to_image(resolution=200).original
                    text = pytesseract.image_to_string(image)
                cleaned = self.parser.clean_content_text(text)
                if cleaned.strip():
                    parts.append(cleaned)
        return "\n\n".join(parts)

    def extract_unmapped_pages(self, pdf, batch_size, use_ocr):
        total = self.parser.total_pdf_pages
        covered = {p for c in self.parser.content_chunks for p in range(c.start_page, c.end_page + 1)}
        missing = [p for p in range(1, total + 1) if p not in covered]
        for page_num in missing:
            page_idx = page_num - 1
            page = pdf.pages[page_idx]
            text = page.extract_text() or ""
            if not text.strip() and use_ocr and OCR_AVAILABLE:
                image = page.to_image(resolution=200).original
                text = pytesseract.image_to_string(image)
            cleaned = self.parser.clean_content_text(text)
            if cleaned.strip():
                chunk = ContentChunk(
                    doc_title=self.parser.doc_title,
                    section_id=f"unmapped-{page_num}",
                    section_path=f"unmapped {page_num}",
                    start_heading=f"Unmapped page {page_num}",
                    start_page=page_num,
                    end_page=page_num,
                    content=cleaned,
                    word_count=len(cleaned.split()),
                )
                self.parser.content_chunks.append(chunk)


# --------------------------
# Main Parser Class
# --------------------------
class USBPDParser:
    def __init__(self, pdf_path: str, doc_title: str = "USB Power Delivery Specification"):
        self.pdf_path = Path(pdf_path)
        self.doc_title = doc_title
        self.toc_entries: List[TocEntry] = []
        self.content_chunks: List[ContentChunk] = []
        self.total_pdf_pages: int = 0
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        self.toc_extractor = TocExtractor(self)
        self.content_extractor = ContentExtractor(self)

    def get_pdf_page_count(self) -> int:
        if self.total_pdf_pages:
            return self.total_pdf_pages
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                self.total_pdf_pages = len(pdf.pages)
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
        return self.total_pdf_pages

    def calculate_level(self, section_id: str) -> int:
        return len(section_id.split("."))

    def get_parent_id(self, section_id: str) -> Optional[str]:
        parts = section_id.split(".")
        return ".".join(parts[:-1]) if len(parts) > 1 else None

    def generate_tags(self, title: str) -> List[str]:
        keywords = {
            "contract": ["contract", "agreement", "capability"],
            "communication": ["communication", "protocol", "message"],
            "power": ["power", "vbus", "voltage", "current"],
            "device": ["device", "source", "sink"],
            "cable": ["cable", "connector", "wire"],
            "testing": ["test", "validation", "verification"],
            "state": ["state", "machine", "transition"],
        }
        tags: List[str] = []
        title_lower = title.lower()
        for tag, terms in keywords.items():
            if any(term in title_lower for term in terms):
                tags.append(tag)
        return tags

    def build_full_path(self, section_id: str, title: str) -> str:
        return f"{section_id} {title}"

    def clean_content_text(self, text: str) -> str:
        lines = text.split("\n")
        cleaned = []
        for line in lines:
            if re.match(r"^\s*\d+\s*$", line):
                continue
            if re.match(r"^Page \d+ of \d+", line, re.I):
                continue
            if line.strip():
                cleaned.append(line)
        return "\n".join(cleaned)

    def find_subsections(self, section_id: str) -> List[str]:
        return [e.section_id for e in self.toc_entries if e.parent_id == section_id]

    def save_jsonl(self, path: str, data: List[Any]) -> None:
        with open(path, "w", encoding="utf-8") as f:
            for item in data:
                f.write(json.dumps(item.to_dict(), ensure_ascii=False) + "\n")

    def generate_statistics(self) -> Dict[str, Any]:
        total_pages = self.total_pdf_pages
        pages_covered = {p for c in self.content_chunks for p in range(c.start_page, c.end_page + 1)}
        total_words = sum(c.word_count for c in self.content_chunks)
        avg_words = total_words / len(self.content_chunks) if self.content_chunks else 0
        coverage = (len(pages_covered) / total_pages * 100) if total_pages else 0
        stats = {
            "total_pages": total_pages,
            "toc_entries": len(self.toc_entries),
            "content_chunks": len(self.content_chunks),
            "total_words": total_words,
            "avg_words_per_section": avg_words,
            "pages_covered": len(pages_covered),
            "coverage_percentage": coverage,
        }
        return stats

    def run(self, config: ParserConfig) -> Dict[str, Any]:
        self.total_pdf_pages = self.get_pdf_page_count()
        toc_text, _ = self.toc_extractor.extract_toc_text(config.scan_all_toc)
        self.toc_entries = self.toc_extractor.parse_toc(toc_text)
        self.save_jsonl(config.output_toc, self.toc_entries)

        if config.extract_content:
            self.content_extractor.extract_full_content(config.batch_size, config.use_ocr)
            self.save_jsonl(config.output_content, self.content_chunks)

        stats = self.generate_statistics()
        self.display_summary(stats)
        return stats

    def display_summary(self, stats: Dict[str, Any]) -> None:
        logger.info("=" * 60)
        logger.info("USB PD Parser Summary")
        logger.info(f"Total Pages: {stats['total_pages']}")
        logger.info(f"TOC Entries: {stats['toc_entries']}")
        logger.info(f"Content Chunks: {stats['content_chunks']}")
        logger.info(f"Total Words: {stats['total_words']}")
        logger.info(f"Pages Covered: {stats['pages_covered']}/{stats['total_pages']}")
        logger.info(f"Avg Words/Section: {stats['avg_words_per_section']:.0f}")
        logger.info(f"Coverage: {stats['coverage_percentage']:.1f}%")
        logger.info("=" * 60)


# --------------------------
# CLI Entry
# --------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description="USB PD Parser v4.0 - Full PDF + OCR")
    parser.add_argument("pdf_path", help="Path to USB PD PDF")
    parser.add_argument("-o", "--output-toc", default="usb_pd_toc.jsonl")
    parser.add_argument("-c", "--output-content", default="usb_pd_content.jsonl")
    parser.add_argument("--title", default="USB Power Delivery Specification")
    parser.add_argument("--extract-content", action="store_true")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--no-scan-all-toc", action="store_true")
    parser.add_argument("--use-ocr", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config = ParserConfig(
        output_toc=args.output_toc,
        output_content=args.output_content,
        extract_content=args.extract_content,
        scan_all_toc=not args.no_scan_all_toc,
        batch_size=args.batch_size,
        use_ocr=args.use_ocr,
    )

    try:
        parser_obj = USBPDParser(args.pdf_path, args.title)
        parser_obj.run(config)
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    exit(main())
