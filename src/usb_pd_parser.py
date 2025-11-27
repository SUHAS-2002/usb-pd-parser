"""
USB Power Delivery Specification Parser - Full Document Version (fixed)
================================================================
Improved to:
- Force full-PDF coverage by extracting unmapped pages
- Create fallback "unmapped-<page>" content chunks
- Correct coverage statistics calculation
- Improved logging and robustness
Version: 3.1 - Full PDF Coverage Fix
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

import pdfplumber

if TYPE_CHECKING:
    from pdfplumber.pdf import PDF

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@dataclass
class TocEntry:
    """Table of Contents entry with full metadata."""

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
    """Represents a parsed content section."""

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
    """Configuration for parser run."""

    output_toc: str = "usb_pd_toc.jsonl"
    output_content: str = "usb_pd_content.jsonl"
    extract_content: bool = True
    scan_all_toc: bool = True
    batch_size: int = 50


@dataclass
class SectionContext:
    """Context object replacing the old 6-parameter function."""
    pdf: "PDF"
    entry: TocEntry
    boundaries: Dict[str, Tuple[int, int]]
    batch_size: int
    idx: int


def roman_to_int(s: str) -> Optional[int]:
    s = s.strip().upper()
    if not s:
        return None
    roman_map = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
    total = 0
    prev = 0
    try:
        for ch in s[::-1]:
            val = roman_map.get(ch, 0)
            if val < prev:
                total -= val
            else:
                total += val
            prev = val
        return total if total > 0 else None
    except Exception:
        return None


class TocExtractor:
    """Handles TOC extraction and parsing."""

    # One main robust regex: leading numeric id (any-depth), title, dot leaders/ellipsis/dashes/spaces, and page number
    TOC_MAIN = re.compile(
        r"^\s*(?P<section_id>\d+(?:\.\d+)*)\.?\s+"
        r"(?P<title>.+?)\s*(?:\.{2,}|…|[\t\-–—]{2,}|\s{2,})\s*(?P<page>(?:\d+|[ivxlcdmIVXLCDM]+))\s*$"
    )
    # Fallback: title ends with page number but id may be embedded earlier
    TOC_FALLBACK = re.compile(
        r"^\s*(?P<line>.+?)\s*(?P<page>(?:\d+|[ivxlcdmIVXLCDM]+))\s*$"
    )

    def __init__(self, parser: "USBPDParser", debug: bool = False):
        self.parser = parser
        self.debug = debug

    def _normalize(self, text: str) -> str:
        # replace NBSP and other weird whitespace characters
        text = text.replace("\u00A0", " ")
        text = re.sub(r'[\u200b\u202f\uFEFF]', '', text)
        return text

    def extract_toc_pages(self, scan_all: bool = True) -> Tuple[str, List[int]]:
        """Extract text from ToC pages - scans entire PDF by default."""
        logger.info(f"Opening PDF: {self.parser.pdf_path}")
        toc_text = ""
        toc_pages: List[int] = []

        try:
            with pdfplumber.open(str(self.parser.pdf_path)) as pdf:
                self.parser.total_pdf_pages = len(pdf.pages)
                logger.info(f"Total pages in PDF: {self.parser.total_pdf_pages}")

                max_scan = (
                    self.parser.total_pdf_pages if scan_all else min(60, self.parser.total_pdf_pages)
                )
                logger.info(f"Scanning first {max_scan} pages for ToC...")

                for i in range(max_scan):
                    if i % 20 == 0:
                        logger.debug(f" Scanning page {i + 1}/{max_scan}...")
                    page = pdf.pages[i]
                    text = page.extract_text() or ""
                    text = self._normalize(text)
                    # Simple heuristics to decide the page is ToC: contains 'contents' or numeric hierarchical tokens with dots
                    has_toc = any(ind in text.lower() for ind in ["table of contents", "contents"])
                    has_numbers = bool(re.search(r"\b\d+(?:\.\d+)+\b", text))
                    if has_toc or has_numbers:
                        toc_text += text + "\n"
                        toc_pages.append(i + 1)
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise

        logger.info(f"Extracted ToC from {len(toc_pages)} pages")
        return toc_text, toc_pages

    def parse_toc_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single ToC line using robust rules and fallbacks."""
        if not line or len(line.strip()) < 3:
            return None
        raw = self._normalize(line).strip()

        # Try main pattern
        m = self.TOC_MAIN.match(raw)
        if m:
            sec_id = m.group("section_id").rstrip(".")
            title = m.group("title").strip()
            page_token = m.group("page").strip()
            if page_token.isdigit():
                page = int(page_token)
            else:
                # Try roman
                rv = roman_to_int(page_token)
                if rv is None:
                    return None
                page = rv
            # Validate section id numeric only
            if not re.match(r"^\d+(?:\.\d+)*$", sec_id):
                return None
            return {"section_id": sec_id, "title": title, "page": page}

        # Fallback: capture title+page, then try to pick id token from earlier tokenized parts
        m2 = self.TOC_FALLBACK.match(raw)
        if m2:
            page_token = m2.group("page").strip()
            if page_token.isdigit():
                page = int(page_token)
            else:
                rv = roman_to_int(page_token)
                if rv is None:
                    return None
                page = rv
            # look for section id anywhere earlier in the line
            # find first token matching id pattern
            tokens = re.split(r"\s+", raw[:-len(page_token)].strip())
            section_id = None
            title_tokens = []
            for t in tokens:
                tt = t.strip(".,;:")
                if re.match(r"^\d+(?:\.\d+)*\.?$", tt):
                    section_id = tt.rstrip(".")
                    continue
                title_tokens.append(tt)
            title = " ".join(title_tokens).strip()
            if section_id:
                return {"section_id": section_id, "title": title, "page": page}

        # Nothing matched
        return None

    def parse_toc(self, toc_text: str, debug_limit: int = 20) -> List[TocEntry]:
        """Parse entire ToC with validation and deduplication."""
        logger.info("Parsing Table of Contents...")
        entries: List[TocEntry] = []
        seen = set()
        unmatched_samples = []
        for line in toc_text.splitlines():
            parsed = self.parse_toc_line(line)
            if not parsed:
                # store some unmatched examples for debugging
                if self.debug and len(unmatched_samples) < debug_limit:
                    s = line.strip()
                    if s:
                        unmatched_samples.append(s)
                continue
            section_id = parsed["section_id"]
            if section_id in seen:
                continue
            seen.add(section_id)
            title = parsed["title"].rstrip(".").strip()
            page = parsed["page"]
            level = self.parser.calculate_level(section_id)
            parent_id = self.parser.get_parent_id(section_id)
            entry = TocEntry(
                doc_title=self.parser.doc_title,
                section_id=section_id,
                title=title,
                full_path=self.parser.build_full_path(section_id, title),
                page=page,
                level=level,
                parent_id=parent_id,
                tags=self.parser.generate_tags(title),
            )
            entries.append(entry)
            self.parser.toc_page_map[section_id] = page

        # Numeric sort by broken out integer parts
        def numeric_sort_key(e: TocEntry):
            return [int(p) for p in e.section_id.split(".")]

        entries.sort(key=numeric_sort_key)
        logger.info(f"Successfully parsed {len(entries)} unique ToC entries")
        if self.debug and unmatched_samples:
            logger.debug("Sample unmatched ToC lines (up to %d):\n%s", len(unmatched_samples), "\n".join(unmatched_samples))
        return entries


class ContentExtractor:
    """Handles content extraction from PDF."""

    def __init__(self, parser: "USBPDParser"):
        self.parser = parser

    def extract_full_content(self, batch_size: int = 50) -> None:
        """Extract complete content from entire PDF."""
        if not self.initialize_extraction():
            return

        try:
            with pdfplumber.open(str(self.parser.pdf_path)) as pdf:
                boundaries = self.build_section_boundaries()

                for idx, entry in enumerate(self.parser.toc_entries, 1):
                    ctx = SectionContext(
                        pdf=pdf,
                        entry=entry,
                        boundaries=boundaries,
                        batch_size=batch_size,
                        idx=idx,
                    )
                    self.process_section_content(ctx)

                self._extract_unmapped_pages(pdf, batch_size)
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            raise

        self.finalize_extraction()

    def initialize_extraction(self) -> bool:
        """Initialize content extraction with validation."""
        logger.info("Extracting FULL document content from ALL pages...")
        if not self.parser.toc_entries:
            logger.warning("No ToC entries found. Run parse_toc first.")
            return False

        if not self.parser.total_pdf_pages:
            self.parser.total_pdf_pages = self.parser.get_pdf_page_count()

        logger.info(f"Processing ALL {self.parser.total_pdf_pages} pages...")
        return True

    def process_section_content(self, ctx: SectionContext) -> None:
        """Extract content for a single section (refactored)."""
        section_id = ctx.entry.section_id
        start_pg, end_pg = ctx.boundaries.get(section_id, (ctx.entry.page, ctx.entry.page))

        if ctx.idx % 10 == 0:
            logger.info(
                f"Processing section {ctx.idx}/{len(self.parser.toc_entries)}: {section_id}"
            )

        content = self.extract_section_batched(ctx.pdf, start_pg, end_pg, ctx.batch_size)
        if not content:
            return

        chunk = ContentChunk(
            doc_title=self.parser.doc_title,
            section_id=section_id,
            section_path=ctx.entry.full_path,
            start_heading=ctx.entry.title,
            start_page=start_pg,
            end_page=end_pg,
            content=content,
            subsections=self.parser.find_subsections(section_id),
            word_count=len(content.split()),
        )
        self.parser.content_chunks.append(chunk)

    def finalize_extraction(self) -> None:
        """Finalize extraction and log results."""
        logger.info(
            f"Extracted {len(self.parser.content_chunks)} content sections from ENTIRE PDF"
        )

    def build_section_boundaries(self) -> Dict[str, Tuple[int, int]]:
        """Build start/end page boundaries for all sections."""
        boundaries: Dict[str, Tuple[int, int]] = {}
        sorted_entries = sorted(self.parser.toc_entries, key=lambda x: x.page)

        for i, entry in enumerate(sorted_entries):
            start_page = entry.page
            end_page = self.find_end_page(sorted_entries, i, entry)
            end_page = min(end_page, self.parser.total_pdf_pages)
            boundaries[entry.section_id] = (start_page, end_page)
            logger.debug(f"Section {entry.section_id}: pages {start_page}-{end_page}")

        return boundaries

    def find_end_page(self, entries: List[TocEntry], index: int, current: TocEntry) -> int:
        """Find end page by looking for next same/higher level section."""
        end_page = self.parser.total_pdf_pages
        for next_entry in entries[index + 1 :]:
            if next_entry.level <= current.level:
                end_page = next_entry.page - 1
                break
        return max(current.page, end_page)

    def extract_section_batched(
        self, pdf: "PDF", start_page: int, end_page: int, batch_size: int
    ) -> str:
        """Extract text from page range in memory-efficient batches."""
        parts: List[str] = []
        start_idx = max(0, start_page - 1)
        end_idx = min(len(pdf.pages), end_page)

        for batch_start in range(start_idx, end_idx, batch_size):
            batch_end = min(batch_start + batch_size, end_idx)
            for page_num in range(batch_start, batch_end):
                if page_num >= len(pdf.pages):
                    break
                page = pdf.pages[page_num]
                text = page.extract_text() or ""
                cleaned = self.parser.clean_content_text(text)
                if cleaned.strip():
                    parts.append(cleaned)

        return "\n\n".join(parts)

    def _extract_unmapped_pages(self, pdf: "PDF", batch_size: int) -> None:
        """Extract pages not covered by any mapped section."""
        total = self.parser.total_pdf_pages
        covered = {
            p
            for c in self.parser.content_chunks
            for p in range(c.start_page, c.end_page + 1)
        }
        missing = [p for p in range(1, total + 1) if p not in covered]

        if not missing:
            logger.info("All pages are covered by ToC sections.")
            return

        logger.info(f"Found {len(missing)} unmapped pages; extracting them individually...")
        for page_num in missing:
            idx = page_num - 1
            if not (0 <= idx < len(pdf.pages)):
                continue
            text = pdf.pages[idx].extract_text() or ""
            cleaned = self.parser.clean_content_text(text)
            if not cleaned.strip():
                continue

            chunk = ContentChunk(
                doc_title=self.parser.doc_title,
                section_id=f"unmapped-{page_num}",
                section_path=f"unmapped {page_num}",
                start_heading=f"Unmapped page {page_num}",
                start_page=page_num,
                end_page=page_num,
                content=cleaned,
                subsections=[],
                word_count=len(cleaned.split()),
            )
            self.parser.content_chunks.append(chunk)


class USBPDParser:
    """Enhanced parser for complete USB PD specification extraction."""

    def __init__(self, pdf_path: str | Path, doc_title: str = "USB Power Delivery Specification"):
        self.pdf_path = Path(pdf_path)
        self.doc_title = doc_title
        self.toc_entries: List[TocEntry] = []
        self.content_chunks: List[ContentChunk] = []
        self.toc_page_map: Dict[str, int] = {}
        self.total_pdf_pages: int = 0

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        self.toc_extractor = TocExtractor(self)
        self.content_extractor = ContentExtractor(self)

    def get_pdf_page_count(self) -> int:
        """Get total page count from PDF."""
        try:
            with pdfplumber.open(str(self.pdf_path)) as pdf:
                return len(pdf.pages)
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            return 0

    def calculate_level(self, section_id: str) -> int:
        return len(section_id.split("."))

    def get_parent_id(self, section_id: str) -> Optional[str]:
        parts = section_id.split(".")
        return ".".join(parts[:-1]) if len(parts) > 1 else None

    def generate_tags(self, title: str) -> List[str]:
        keywords = {
            "contract": ["contract", "negotiation", "agreement", "capability"],
            "communication": ["communication", "message", "protocol", "data"],
            "device": ["device", "source", "sink", "drp", "port"],
            "power": ["power", "voltage", "current", "vbus", "supply"],
            "cable": ["cable", "plug", "connector", "wire"],
            "collision": ["collision", "avoidance", "detect"],
            "revision": ["revision", "compatibility", "version", "legacy"],
            "requirements": ["requirement", "shall", "must", "mandatory"],
            "testing": ["test", "validation", "verification", "compliance"],
            "state": ["state", "machine", "transition", "mode"],
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
        cleaned: List[str] = []
        for line in lines:
            if re.match(r"^\s*\d+\s*$", line):
                continue
            if re.match(r"^Page \d+ of \d+", line, re.IGNORECASE):
                continue
            if re.match(r"^\s*USB Power Delivery", line, re.IGNORECASE):
                continue
            if line.strip():
                cleaned.append(line)
        return "\n".join(cleaned)

    def find_subsections(self, section_id: str) -> List[str]:
        return [e.section_id for e in self.toc_entries if e.parent_id == section_id]

    def save_toc_jsonl(self, output_path: str) -> None:
        path = Path(output_path)
        logger.info(f"Writing ToC to: {path}")
        try:
            with path.open("w", encoding="utf-8") as f:
                for entry in self.toc_entries:
                    f.write(json.dumps(entry.to_dict(), ensure_ascii=False) + "\n")
            logger.info(f"Wrote {len(self.toc_entries)} ToC entries")
        except Exception as e:
            logger.error(f"Error writing ToC JSONL: {e}")
            raise

    def save_content_jsonl(self, output_path: str) -> None:
        path = Path(output_path)
        logger.info(f"Writing content to: {path}")
        try:
            with path.open("w", encoding="utf-8") as f:
                for chunk in self.content_chunks:
                    f.write(json.dumps(chunk.to_dict(), ensure_ascii=False) + "\n")
            total_words = sum(c.word_count for c in self.content_chunks)
            logger.info(f"Wrote {len(self.content_chunks)} content chunks")
            logger.info(f"Total content: {total_words:,} words extracted")
        except Exception as e:
            logger.error(f"Error writing content JSONL: {e}")
            raise

    def generate_statistics(self) -> Dict[str, Any]:
        stats: Dict[str, Any] = {
            "pdf_info": {"total_pages": self.total_pdf_pages, "file_path": str(self.pdf_path)},
            "toc_statistics": {
                "total_entries": len(self.toc_entries),
                "by_level": defaultdict(int),
                "page_range": {
                    "min": min((e.page for e in self.toc_entries), default=0),
                    "max": max((e.page for e in self.toc_entries), default=0),
                },
            },
            "content_statistics": {
                "total_chunks": len(self.content_chunks),
                "total_words": sum(c.word_count for c in self.content_chunks),
                "avg_words_per_section": 0,
                "coverage_percentage": 0,
                "pages_covered": 0,
            },
        }

        for entry in self.toc_entries:
            stats["toc_statistics"]["by_level"][entry.level] += 1

        if self.content_chunks:
            cs = stats["content_statistics"]
            cs["avg_words_per_section"] = cs["total_words"] / len(self.content_chunks)
            pages = {
                p
                for c in self.content_chunks
                for p in range(c.start_page, c.end_page + 1)
            }
            cs["pages_covered"] = len(pages)
            total_pages = self.total_pdf_pages or stats["pdf_info"]["total_pages"]
            if total_pages > 0:
                cs["coverage_percentage"] = (len(pages) / total_pages) * 100

        return stats

    def run(self, config: ParserConfig) -> Dict[str, Any]:
        logger.info("=" * 70)
        logger.info("USB PD Parser v3.1 - FULL PDF EXTRACTION (coverage fixes)")
        logger.info("=" * 70)

        self.total_pdf_pages = self.get_pdf_page_count()
        logger.info(f"PDF has {self.total_pdf_pages} total pages")

        # Set debug on toc_extractor if needed
        if config.scan_all_toc and hasattr(self.toc_extractor, "debug"):
            self.toc_extractor.debug = True if config.scan_all_toc else False

        toc_text, _ = self.toc_extractor.extract_toc_pages(config.scan_all_toc)
        self.toc_entries = self.toc_extractor.parse_toc(toc_text)

        if not self.toc_entries:
            logger.error("No ToC entries found! Check PDF format.")
            return {}

        self.save_toc_jsonl(config.output_toc)

        if config.extract_content:
            self.content_extractor.extract_full_content(config.batch_size)
            self.save_content_jsonl(config.output_content)

        stats = self.generate_statistics()
        self.display_summary(stats)

        logger.info("=" * 70)
        logger.info("COMPLETE PARSING FINISHED!")
        logger.info("=" * 70)
        return stats

    def display_summary(self, stats: Dict[str, Any]) -> None:
        logger.info("\n" + "=" * 70)
        logger.info("COMPLETE PARSING SUMMARY")
        logger.info("=" * 70)

        pdf = stats["pdf_info"]
        logger.info(f"PDF: {pdf['total_pages']} total pages")

        toc = stats["toc_statistics"]
        logger.info(f"\nToC Entries: {toc['total_entries']}")
        logger.info(f"Page Range: {toc['page_range']['min']} - {toc['page_range']['max']}")
        logger.info("Entries by Level:")
        for level, count in sorted(toc["by_level"].items()):
            logger.info(f" Level {level}: {count} sections")

        if stats["content_statistics"]["total_chunks"] > 0:
            cs = stats["content_statistics"]
            logger.info(f"\nContent Extraction:")
            logger.info(f" Sections Extracted: {cs['total_chunks']}")
            logger.info(f" Total Words: {cs['total_words']:,}")
            logger.info(f" Pages Covered: {cs['pages_covered']}/{pdf['total_pages']}")
            logger.info(f" Avg Words/Section: {cs['avg_words_per_section']:.0f}")
            logger.info(f" Coverage: {cs['coverage_percentage']:.1f}%")

def main() -> int:
    parser = argparse.ArgumentParser(
        description="USB PD Parser v3.1 - COMPLETE PDF Extraction (1000+ pages)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s spec.pdf --extract-content
  %(prog)s spec.pdf --extract-content --batch-size 100
  %(prog)s spec.pdf -o toc.jsonl
        """,
    )
    parser.add_argument("pdf_path", help="Path to USB PD specification PDF")
    parser.add_argument("-o", "--output-toc", default="usb_pd_toc.jsonl")
    parser.add_argument("-c", "--output-content", default="usb_pd_content.jsonl")
    parser.add_argument("-t", "--title", default="USB Power Delivery Specification")
    parser.add_argument("--extract-content", action="store_true")
    parser.add_argument("--batch-size", type=int, default=50)
    parser.add_argument("--no-scan-all-toc", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        pd_parser = USBPDParser(args.pdf_path, args.title)
        config = ParserConfig(
            output_toc=args.output_toc,
            output_content=args.output_content,
            extract_content=args.extract_content,
            scan_all_toc=not args.no_scan_all_toc,
            batch_size=args.batch_size,
        )
        pd_parser.run(config)
        return 0
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    exit(main())