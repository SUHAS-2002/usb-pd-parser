"""
TOC extractor (compact OOP, ≤79 chars).

Extracts TOC entries and synthesizes numeric section IDs
by aligning TOC pages with body section headings.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple

from src.config import CONFIG


# ------------------------------------------------------------------
# Data model
# ------------------------------------------------------------------
@dataclass(frozen=True)
class TocEntry:
    doc_title: str
    section_id: str
    title: str
    page: int
    level: int
    parent_id: Optional[str]
    full_path: str
    tags: List[str]


# ------------------------------------------------------------------
# Extractor
# ------------------------------------------------------------------
class ToCExtractor:
    """
    Semantic TOC extractor for USB-PD PDF.

    Encapsulation:
    - Minimal public API (`extract`)
    - All helpers are private
    - Regex patterns are private class constants
    """

    # --------------------------------------------------------------
    # Private regex patterns
    # --------------------------------------------------------------
    _BODY_SECTION_RE = re.compile(
        r"^\s*(\d+(?:\.\d+)*)\s+(.+)$",
        re.MULTILINE,
    )

    _FRONT_RE = re.compile(
        r"^\s*([A-Za-z][A-Za-z\s]+?)\.{3,}\s*(\d{1,4})\s*$"
    )

    _NUMBERED_TOC_RE = re.compile(
        r"^\s*(\d+(?:\.\d+)*)\s+(.+?)\s*\.{2,}\s*(\d+)\s*$"
    )

    _APPENDIX_TOC_RE = re.compile(
        r"^\s*([A-E](?:\.\d+)*)\s+(.+?)\s*\.{2,}\s*(\d+)\s*$"
    )

    _FIGURE_TOC_RE = re.compile(
        r"^\s*(Figure\s+\d+(?:\.\d+)*)\s+(.+?)\s*\.{2,}\s*(\d+)\s*$"
    )

    _TABLE_TOC_RE = re.compile(
        r"^\s*(Table\s+\d+(?:\.\d+)*)\s+(.+?)\s*\.{2,}\s*(\d+)\s*$"
    )

    _TOC_HEADER_RE = re.compile(
        r"\btable\s+of\s+contents\b",
        re.IGNORECASE,
    )

    _SELF_REF_RE = re.compile(
        r"^\s*table\s+of\s+contents\s*\.{3,}",
        re.IGNORECASE,
    )

    # --------------------------------------------------------------
    def __init__(self) -> None:
        self._doc_title: str = CONFIG.DOC_TITLE
        self._max_page: int = CONFIG.pages.MAX_PAGE

    # --------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------
    def extract(self, pages: List[Dict]) -> List[Dict]:
        toc_entries = self._extract_toc_pages(pages)
        body_sections = self._extract_all_numeric_headings(pages)

        merged = self._merge_toc_with_sections(
            toc_entries,
            body_sections,
        )

        ordered = sorted(
            merged.values(),
            key=lambda e: (e.page, self._sid_key(e.section_id)),
        )

        return [asdict(e) for e in ordered]

    # --------------------------------------------------------------
    # TOC page extraction
    # --------------------------------------------------------------
    def _extract_toc_pages(
        self,
        pages: List[Dict],
    ) -> Dict[str, TocEntry]:
        entries: Dict[str, TocEntry] = {}
        in_toc = False

        for page in pages:
            page_num = page.get("page", 0)
            text = page.get("text") or ""

            if self._TOC_HEADER_RE.search(text):
                in_toc = True

            if not self._is_valid_toc_page(in_toc, page_num):
                continue

            for sid, title, pg in self._parse_page(text):
                if self._is_valid_entry(sid, title, pg):
                    entries[sid] = self._make_entry(
                        sid,
                        title,
                        pg,
                    )

        return entries

    # --------------------------------------------------------------
    # Page parsing helpers
    # --------------------------------------------------------------
    def _is_valid_toc_page(
        self,
        in_toc: bool,
        page_num: int,
    ) -> bool:
        """Check if page is within the TOC page range."""
        return (
            in_toc
            and CONFIG.pages.TOC_START <= page_num <= CONFIG.pages.TOC_END
        )

    def _parse_page(
        self,
        text: str,
    ) -> List[Tuple[Optional[str], str, int]]:
        parsed: List[Tuple[Optional[str], str, int]] = []

        for line in self._clean_lines(text):
            item = self._parse_toc_line(line)
            if item:
                parsed.append(item)

        return parsed

    def _clean_lines(self, text: str) -> List[str]:
        """Remove self-referential TOC lines."""
        return [
            ln for ln in text.splitlines()
            if not self._SELF_REF_RE.match(ln)
        ]

    def _parse_toc_line(
        self,
        line: str,
    ) -> Optional[Tuple[Optional[str], str, int]]:
        for rx in (
            self._NUMBERED_TOC_RE,
            self._APPENDIX_TOC_RE,
            self._FIGURE_TOC_RE,
            self._TABLE_TOC_RE,
        ):
            match = rx.match(line)
            if match:
                sid, title, page = match.groups()
                return (
                    sid,
                    title.strip().rstrip("."),
                    int(page),
                )

        front = self._FRONT_RE.match(line)
        if front:
            title, page = front.groups()
            return None, title.strip(), int(page)

        return None

    def _is_valid_entry(
        self,
        sid: Optional[str],
        title: str,
        page: int,
    ) -> bool:
        if not sid:
            return False
        if page > self._max_page:
            return False
        return not self._is_false_positive(title)

    @staticmethod
    def _is_false_positive(title: str) -> bool:
        return title.lower().strip() in {
            "version",
            "version:",
            "release date:",
            "v1.0",
            "v1.1",
            "v2.0",
            "v3.0",
            "v3.1",
            "v3.2",
        }

    # --------------------------------------------------------------
    # Numeric heading extraction
    # --------------------------------------------------------------
    def _extract_all_numeric_headings(
        self,
        pages: List[Dict],
    ) -> Dict[str, Tuple[str, int]]:
        sections: Dict[str, Tuple[str, int]] = {}

        for page in pages:
            page_no = page.get("page", 0)
            text = page.get("text") or ""

            for match in self._BODY_SECTION_RE.finditer(text):
                sid, title = match.groups()
                sections.setdefault(
                    sid,
                    (title.strip(), page_no),
                )

        return sections

    def _merge_toc_with_sections(
        self,
        toc: Dict[str, TocEntry],
        sections: Dict[str, Tuple[str, int]],
    ) -> Dict[str, TocEntry]:
        merged = dict(toc)

        for sid, (title, page) in sections.items():
            if sid not in merged:
                merged[sid] = self._make_entry(
                    sid,
                    title,
                    page,
                )

        return merged

    # --------------------------------------------------------------
    # Entry helpers
    # --------------------------------------------------------------
    def _make_entry(
        self,
        sid: str,
        title: str,
        page: int,
    ) -> TocEntry:
        level = sid.count(".") + 1
        parent = sid.rsplit(".", 1)[0] if "." in sid else None

        return TocEntry(
            doc_title=self._doc_title,
            section_id=sid,
            title=title,
            page=page,
            level=level,
            parent_id=parent,
            full_path=f"{sid} {title}",
            tags=self._infer_tags(title),
        )

    @staticmethod
    def _sid_key(sid: str) -> List[int]:
        return [int(p) for p in sid.split(".") if p.isdigit()]

    def _infer_tags(self, title: str) -> List[str]:
        t = title.lower()
        tags: List[str] = []

        if any(w in t for w in ("power", "voltage", "current", "vbus")):
            tags.append("power")

        if any(
            w in t
            for w in ("source", "sink", "device", "port", "cable", "plug")
        ):
            tags.append("device")

        if any(w in t for w in ("state", "transition", "mode")):
            tags.append("state")

        if any(
            w in t
            for w in ("message", "protocol", "sop", "communication")
        ):
            tags.append("comm")

        return tags
