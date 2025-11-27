#!/usr/bin/env python3
"""
usb_pd_parser_final.py

Robust ToC-aware PDF parser tuned for USB_PD_R3_2 V1.1 2024-10 layout.
Saves: toc jsonl and content jsonl.

Features:
- robust ToC line parsing (multiple regex strategies)
- correct boundary logic (include deeper subsections)
- verbose debug mode to show which ToC lines were accepted/rejected
- OCR fallback (optional)
"""

import argparse
import json
import logging
import re
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pdfplumber

# optional OCR
try:
    from pdf2image import convert_from_path
    import pytesseract

    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class TocEntry:
    doc_title: str
    section_id: str
    title: str
    full_path: str
    page: int
    level: int
    parent_id: Optional[str]
    tags: List[str] = field(default_factory=list)

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
    word_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ParserConfig:
    output_toc: str = "usb_pd_toc.jsonl"
    output_content: str = "usb_pd_content.jsonl"
    extract_content: bool = True
    scan_all_toc: bool = True
    toc_scan_pages: int = 75
    batch_size: int = 50
    use_ocr: bool = False
    verbose: bool = False
    save_debug_lines: Optional[str] = None


def numeric_section_key(section_id: str) -> Tuple[int, ...]:
    parts = re.findall(r"\d+", section_id)
    return tuple(int(p) for p in parts) if parts else (999999,)


class TocExtractor:
    """
    Very tolerant ToC parsing:
    - tries several regex patterns (dotted leaders, spaces, colons)
    - fallback: find trailing page number and a leading section id
    - provides debug logging for accepted/rejected candidates
    """

    # multiple tolerant patterns
    PATTERNS = [
        r"^(\d+(?:\.\d+)+)\s+(.+?)\s+\.{2,}\s*(\d{1,4})\s*$",  # 8.2.7  Title ....... 423
        r"^(\d+(?:\.\d+)+)\s+(.+?)\s{2,}(\d{1,4})\s*$",         # 8.2.7  Title   423
        r"^(\d+(?:\.\d+)+)\s*[:\-]\s*(.+?)\s+\.{2,}\s*(\d{1,4})\s*$",
        r"^(\d+(?:\.\d+)+)\s+(.+?)\s+(\d{1,4})\s*$",            # generic: ends with number
        r"^(\d+)\s+(.+?)\s+\.{2,}\s*(\d{1,4})\s*$",             # top-level single integer
    ]

    def _init_(self, parser: "USBPDParser"):
        self.parser = parser
        self.compiled = [re.compile(p) for p in self.PATTERNS]

    def extract_toc_pages(self, scan_all: bool = True, max_pages: int = 75) -> Tuple[str, List[int]]:
        toc_text = ""
        toc_pages: List[int] = []
        with pdfplumber.open(self.parser.pdf_path) as pdf:
            total = len(pdf.pages)
            limit = total if scan_all else min(max_pages, total)
            logger.info(f"Scanning first {limit} pages for ToC-like content (total pages: {total})")
            for i in range(limit):
                page = pdf.pages[i]
                text = page.extract_text() or ""
                low = text.lower()
                # heuristics: "table of contents" OR many dotted leaders OR lines starting with numerics
                if "table of contents" in low or re.search(r"\.{2,}", text) or re.search(r"^\s*\d+(?:\.\d+)+\s+", text, re.MULTILINE):
                    toc_text += text + "\n"
                    toc_pages.append(i + 1)
        logger.info(f"Collected ToC-like text from {len(toc_pages)} pages")
        return toc_text, toc_pages

    def parse_toc_line(self, line: str) -> Optional[Dict[str, Any]]:
        s = line.strip()
        if not s or len(s) < 3:
            return None
        # Try the strict patterns first
        for cre in self.compiled:
            m = cre.match(s)
            if not m:
                continue
            sid = m.group(1).strip()
            title = m.group(2).strip()
            page = m.group(3).strip()
            try:
                page_num = int(page)
            except Exception:
                continue
            title = re.sub(r"\.{2,}", "", title).strip()
            return {"section_id": sid, "title": title, "page": page_num}

        # fallback: try to capture a trailing page number and a leading section id anywhere
        # e.g. "   8.2.7    Interface to the Policy Engine .................. 423"
        m2 = re.search(r"(\d{1,4})\s*$", s)
        m1 = re.match(r"\s*(\d+(?:\.\d+)+)\s+(.+?)\s+\d{1,4}\s*$", s)
        if m1 and m2:
            sid = m1.group(1).strip()
            title = m1.group(2).strip()
            try:
                page_num = int(m2.group(1))
            except Exception:
                return None
            title = re.sub(r"\.{2,}", "", title).strip()
            return {"section_id": sid, "title": title, "page": page_num}

        return None

    def parse_toc(self, toc_text: str, debug_save: Optional[str] = None) -> List[TocEntry]:
        lines = toc_text.splitlines()
        entries: List[TocEntry] = []
        seen = set()
        rejected = []
        accepted_debug = []

        for ln in lines:
            parsed = self.parse_toc_line(ln)
            if parsed:
                sid = parsed["section_id"]
                if sid in seen:
                    continue
                seen.add(sid)
                entry = TocEntry(
                    doc_title=self.parser.doc_title,
                    section_id=sid,
                    title=parsed["title"],
                    full_path=self.parser.build_full_path(sid, parsed["title"]),
                    page=parsed["page"],
                    level=self.parser.calculate_level(sid),
                    parent_id=self.parser.get_parent_id(sid),
                    tags=self.parser.generate_tags(parsed["title"]),
                )
                entries.append(entry)
                accepted_debug.append((ln, parsed))
                self.parser.toc_page_map[sid] = parsed["page"]
            else:
                # collect rejections for debug
                rejected.append(ln)

        # stable sort by page then numeric section
        entries.sort(key=lambda e: (e.page, numeric_section_key(e.section_id)))

        if debug_save:
            with open(debug_save, "w", encoding="utf-8") as f:
                f.write("=== Accepted ToC Lines ===\n")
                for l, p in accepted_debug:
                    f.write(json.dumps({"line": l, "parsed": p}, ensure_ascii=False) + "\n")
                f.write("\n=== Rejected Lines ===\n")
                for r in rejected:
                    f.write(json.dumps({"line": r}, ensure_ascii=False) + "\n")
            logger.info(f"Debug ToC candidate report saved to: {debug_save}")

        logger.info(f"Parsed {len(entries)} ToC entries")
        return entries


class ContentExtractor:
    def _init_(self, parser: "USBPDParser"):
        self.parser = parser

    def build_section_boundaries(self) -> Dict[str, Tuple[int, int]]:
        boundaries = {}
        entries = sorted(self.parser.toc_entries, key=lambda e: (e.page, numeric_section_key(e.section_id)))
        total_pages = self.parser.total_pdf_pages or self.parser.get_pdf_page_count()

        for idx, entry in enumerate(entries):
            start = entry.page
            end = total_pages
            # find next sibling or parent-level entry to limit end page
            for nxt in entries[idx + 1:]:
                # if nxt is a deeper child of entry, skip
                if nxt.section_id.startswith(entry.section_id + "."):
                    continue
                # if nxt is same level or shallower -> end before that
                if nxt.level <= entry.level:
                    end = nxt.page - 1
                    break
                # fallback: if not child (different branch) but still appears later, end before it
                if not nxt.section_id.startswith(entry.section_id + "."):
                    end = nxt.page - 1
                    break
            end = max(start, min(end, total_pages))
            boundaries[entry.section_id] = (start, end)
            logger.debug(f"Boundary {entry.section_id}: {start}-{end}")
        return boundaries

    def extract_text_from_pages(self, pdf, start_page:int, end_page:int, batch_size:int, use_ocr:bool):
        parts = []
        start_idx = max(0, start_page - 1)
        end_idx = min(len(pdf.pages), end_page)
        for bstart in range(start_idx, end_idx, batch_size):
            bend = min(bstart + batch_size, end_idx)
            for pnum in range(bstart, bend):
                page = pdf.pages[pnum]
                text = page.extract_text() or ""
                if not text and use_ocr:
                    text = self.parser.ocr_page(self.parser.pdf_path, pnum + 1) or ""
                cleaned = self.parser.clean_content_text(text)
                if cleaned.strip():
                    parts.append(cleaned)
        return "\n\n".join(parts)

    def extract_full_content(self, batch_size:int=50, use_ocr:bool=False):
        if not self.parser.toc_entries:
            logger.warning("No ToC entries; extracting unmapped pages only.")
            return
        with pdfplumber.open(self.parser.pdf_path) as pdf:
            boundaries = self.build_section_boundaries()
            for idx, entry in enumerate(self.parser.toc_entries, 1):
                start, end = boundaries.get(entry.section_id, (entry.page, entry.page))
                if idx % 20 == 0:
                    logger.info(f"Processing section {idx}/{len(self.parser.toc_entries)}: {entry.section_id} ({start}-{end})")
                content = self.extract_text_from_pages(pdf, start, end, batch_size, use_ocr)
                if not content.strip():
                    continue
                chunk = ContentChunk(
                    doc_title=self.parser.doc_title,
                    section_id=entry.section_id,
                    section_path=entry.full_path,
                    start_heading=entry.title,
                    start_page=start,
                    end_page=end,
                    content=content,
                    subsections=self.parser.find_subsections(entry.section_id),
                    word_count=len(content.split()),
                )
                self.parser.content_chunks.append(chunk)
            # unmapped pages
            total = self.parser.total_pdf_pages or len(pdf.pages)
            covered = {p for c in self.parser.content_chunks for p in range(c.start_page, c.end_page + 1)}
            missing = [p for p in range(1, total+1) if p not in covered]
            if missing:
                logger.info(f"Extracting {len(missing)} unmapped pages")
                for p in missing:
                    idx = p-1
                    if idx < 0 or idx >= len(pdf.pages): continue
                    text = pdf.pages[idx].extract_text() or ""
                    if not text and use_ocr:
                        text = self.parser.ocr_page(self.parser.pdf_path, p) or ""
                    cleaned = self.parser.clean_content_text(text)
                    if cleaned.strip():
                        chunk = ContentChunk(
                            doc_title=self.parser.doc_title,
                            section_id=f"unmapped-{p}",
                            section_path=f"unmapped {p}",
                            start_heading=f"Unmapped page {p}",
                            start_page=p,
                            end_page=p,
                            content=cleaned,
                            subsections=[],
                            word_count=len(cleaned.split()),
                        )
                        self.parser.content_chunks.append(chunk)


class USBPDParser:
    def _init_(self, pdf_path: str, doc_title: str = "USB Power Delivery Specification"):
        self.pdf_path = Path(pdf_path)
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
        self.doc_title = doc_title
        self.toc_entries: List[TocEntry] = []
        self.content_chunks: List[ContentChunk] = []
        self.toc_page_map: Dict[str,int] = {}
        self.total_pdf_pages: int = 0

        self.toc_extractor = TocExtractor(self)
        self.content_extractor = ContentExtractor(self)

    def get_pdf_page_count(self) -> int:
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                return len(pdf.pages)
        except Exception:
            logger.exception("Could not read PDF")
            return 0

    def calculate_level(self, section_id: str) -> int:
        return len(section_id.split("."))

    def get_parent_id(self, section_id: str) -> Optional[str]:
        parts = section_id.split(".")
        return ".".join(parts[:-1]) if len(parts) > 1 else None

    def generate_tags(self, title: str) -> List[str]:
        kws = {
            "power": ["power","vbus","supply","voltage","current"],
            "policy": ["policy","policy engine","device policy"],
            "state": ["state","state diagram","transition"],
            "message": ["message","capabilities","request","accept","reject"],
        }
        t = (title or "").lower()
        return [k for k,v in kws.items() if any(w in t for w in v)]

    def build_full_path(self, section_id: str, title: str) -> str:
        return f"{section_id} {title}"

    def clean_content_text(self, text: str) -> str:
        if not text:
            return ""
        lines = text.splitlines()
        out = []
        for ln in lines:
            if re.match(r"^\s*Page\s+\d+\s*(of\s+\d+)?\s*$", ln, re.I):
                continue
            if re.match(r"^\s*\d+\s*$", ln):
                continue
            out.append(ln.rstrip())
        return "\n".join(out)

    def find_subsections(self, section_id: str) -> List[str]:
        return [e.section_id for e in self.toc_entries if e.section_id.startswith(section_id + ".")]

    def ocr_page(self, pdf_path: Path, page_number: int) -> Optional[str]:
        if not OCR_AVAILABLE:
            logger.error("OCR not available")
            return None
        try:
            images = convert_from_path(str(pdf_path), first_page=page_number, last_page=page_number)
            if not images: return None
            img = images[0]
            text = pytesseract.image_to_string(img)
            return text
        except Exception:
            logger.exception("OCR failed")
            return None

    def save_toc_jsonl(self, outpath: str):
        with open(outpath, "w", encoding="utf-8") as f:
            for e in self.toc_entries:
                f.write(json.dumps(e.to_dict(), ensure_ascii=False) + "\n")
        logger.info(f"Saved ToC -> {outpath}")

    def save_content_jsonl(self, outpath: str):
        with open(outpath, "w", encoding="utf-8") as f:
            for c in self.content_chunks:
                f.write(json.dumps(c.to_dict(), ensure_ascii=False) + "\n")
        logger.info(f"Saved content -> {outpath}")

    def generate_statistics(self) -> Dict[str,Any]:
        stats = {
            "total_pages": self.total_pdf_pages,
            "toc_entries": len(self.toc_entries),
            "content_chunks": len(self.content_chunks),
            "total_words": sum(c.word_count for c in self.content_chunks),
        }
        return stats

    def run(self, config: ParserConfig):
        logger.setLevel(logging.DEBUG if config.verbose else logging.INFO)
        logger.info("Starting parser run")
        self.total_pdf_pages = self.get_pdf_page_count()
        logger.info(f"PDF pages: {self.total_pdf_pages}")

        toc_text, toc_pages = self.toc_extractor.extract_toc_pages(scan_all=config.scan_all_toc, max_pages=config.toc_scan_pages)
        if not toc_text.strip():
            logger.warning("No ToC text found in scanned range")
            self.toc_entries = []
        else:
            self.toc_entries = self.toc_extractor.parse_toc(toc_text, debug_save=config.save_debug_lines)

        if self.toc_entries:
            self.save_toc_jsonl(config.output_toc)
        else:
            logger.warning("No ToC entries parsed; content extraction will attempt unmapped page extraction")

        if config.extract_content:
            self.content_extractor.extract_full_content(batch_size=config.batch_size, use_ocr=config.use_ocr)
            self.save_content_jsonl(config.output_content)

        stats = self.generate_statistics()
        logger.info(f"Done. Stats: {stats}")
        return stats


def main():
    ap = argparse.ArgumentParser(description="usb_pd_parser_final.py")
    ap.add_argument("pdf_path")
    ap.add_argument("--extract-content", action="store_true")
    ap.add_argument("--ocr", action="store_true")
    ap.add_argument("--no-scan-all-toc", action="store_true")
    ap.add_argument("--scan-pages", type=int, default=75)
    ap.add_argument("--batch-size", type=int, default=50)
    ap.add_argument("-v", "--verbose", action="store_true")
    ap.add_argument("--output-toc", default="usb_pd_toc.jsonl")
    ap.add_argument("--output-content", default="usb_pd_content.jsonl")
    ap.add_argument("--debug-toc-lines", default="toc_debug.jsonl", help="save accepted/rejected ToC lines for debugging")
    args = ap.parse_args()

    if args.ocr and not OCR_AVAILABLE:
        logger.error("OCR requested but dependencies missing (pdf2image/pytesseract)")
        return 2

    cfg = ParserConfig(
        output_toc=args.output_toc,
        output_content=args.output_content,
        extract_content=args.extract_content,
        scan_all_toc=not args.no_scan_all_toc,
        toc_scan_pages=args.scan_pages,
        batch_size=args.batch_size,
        use_ocr=args.ocr,
        verbose=args.verbose,
        save_debug_lines=args.debug_toc_lines,
    )

    parser = USBPDParser(args.pdf_path)
    parser.run(cfg)
    return 0


if _name_ == "_main_":
    raise SystemExit(main())