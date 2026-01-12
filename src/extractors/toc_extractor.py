"""
TOC extractor (compact OOP, ≤79 chars).

Extracts TOC entries and synthesizes numeric section IDs
by aligning TOC pages with body section headings.
"""

import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple


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

    def __str__(self) -> str:
        return f"{self.section_id}: {self.title} (page {self.page})"

    def __repr__(self) -> str:
        return (
            "TocEntry("
            f"section_id={self.section_id!r}, "
            f"page={self.page}, level={self.level}"
            ")"
        )

    def __len__(self) -> int:
        return len(self.title)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TocEntry):
            return NotImplemented
        return (
            self.section_id == other.section_id
            and self.page == other.page
        )


# ------------------------------------------------------------------
# Extractor
# ------------------------------------------------------------------
class ToCExtractor:
    """Semantic TOC extractor for USB-PD PDF."""

    BODY_SECTION_RE = re.compile(
        r"^\s*(\d+(?:\.\d+)*)\s+(.+)$",
        re.MULTILINE,
    )

    FRONT_RE = re.compile(
        r"^\s*([A-Za-z][A-Za-z\s]+?)\.{3,}\s*(\d{1,4})\s*$"
    )

    NUMBERED_TOC_RE = re.compile(
        r"^\s*(\d+(?:\.\d+)*)\s+(.+?)\s*\.{2,}\s*(\d+)\s*$"
    )

    APPENDIX_TOC_RE = re.compile(
        r"^\s*([A-E](?:\.\d+)*)\s+(.+?)\s*\.{2,}\s*(\d+)\s*$"
    )

    FIGURE_TOC_RE = re.compile(
        r"^\s*(Figure\s+\d+(?:\.\d+)*)\s+(.+?)\s*\.{2,}\s*(\d+)\s*$"
    )

    TABLE_TOC_RE = re.compile(
        r"^\s*(Table\s+\d+(?:\.\d+)*)\s+(.+?)\s*\.{2,}\s*(\d+)\s*$"
    )

    TOC_HEADER_RE = re.compile(
        r"\btable\s+of\s+contents\b",
        re.IGNORECASE,
    )

    SELF_REF_RE = re.compile(
        r"^\s*table\s+of\s+contents\s*\.{3,}",
        re.IGNORECASE,
    )

    # --------------------------------------------------------------
    def __init__(self) -> None:
        self._doc_title: str = "USB Power Delivery Specification"
        self._max_real_page: int = 1100

    @property
    def doc_title(self) -> str:
        return self._doc_title

    @property
    def max_real_page(self) -> int:
        return self._max_real_page

    # --------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------
    def extract(self, pages: List[Dict]) -> List[Dict]:
        toc_entries = self._extract_toc_pages(pages)
        all_sections = self._extract_all_numeric_headings(pages)
        merged = self._merge_toc_with_sections(
            toc_entries,
            all_sections,
        )

        items = sorted(
            merged.values(),
            key=lambda e: (e.page, self._sid_key(e.section_id)),
        )

        return [asdict(e) for e in items]

    # --------------------------------------------------------------
    # TOC extraction (front matter)
    # --------------------------------------------------------------
    def _extract_toc_pages(
        self,
        pages: List[Dict],
    ) -> Dict[str, TocEntry]:
        entries: Dict[str, TocEntry] = {}
        in_toc = False

        for pg in pages:
            text = pg.get("text", "") or ""

            if self.TOC_HEADER_RE.search(text):
                in_toc = True

            if not in_toc:
                continue

            lines = [
                ln for ln in text.splitlines()
                if not self.SELF_REF_RE.match(ln)
            ]

            for sid, title, p in self._from_page("\n".join(lines)):
                if p > self.max_real_page:
                    continue

                # ✅ FIX 2: never drop entries
                if sid:
                    entries[sid] = self._make_entry(sid, title, p)
                else:
                    temp_id = f"TEMP:page={p}:idx={len(entries)}"
                    entries[temp_id] = self._make_entry(
                        temp_id, title, p
                    )

        return entries

    # --------------------------------------------------------------
    # Full document numeric heading extraction
    # --------------------------------------------------------------
    def _extract_all_numeric_headings(
        self,
        pages: List[Dict],
    ) -> Dict[str, Tuple[str, int]]:
        sections: Dict[str, Tuple[str, int]] = {}

        for pg in pages:
            text = pg.get("text", "") or ""
            page_no = pg.get("page", 0)

            for m in self.BODY_SECTION_RE.finditer(text):
                sid, title = m.groups()
                sections.setdefault(
                    sid,
                    (title.strip(), page_no),
                )

        return sections

    # --------------------------------------------------------------
    # Merge logic
    # --------------------------------------------------------------
    def _merge_toc_with_sections(
        self,
        toc_entries: Dict[str, TocEntry],
        all_sections: Dict[str, Tuple[str, int]],
    ) -> Dict[str, TocEntry]:
        merged = dict(toc_entries)

        for sid, (title, page) in all_sections.items():
            if sid not in merged:
                merged[sid] = self._make_entry(
                    sid, title, page
                )

        return merged

    # --------------------------------------------------------------
    # Internals
    # --------------------------------------------------------------
    def _from_page(
        self,
        text: str,
    ) -> List[Tuple[Optional[str], str, int]]:
        out: List[Tuple[Optional[str], str, int]] = []

        for ln in text.splitlines():
            sid = None
            title = None
            page = None

            for rx in (
                self.NUMBERED_TOC_RE,
                self.APPENDIX_TOC_RE,
                self.FIGURE_TOC_RE,
                self.TABLE_TOC_RE,
            ):
                m = rx.match(ln)
                if m:
                    sid, t, p = m.groups()
                    title = t.strip().rstrip(".").strip()
                    page = int(p)
                    break

            if not title:
                m = self.FRONT_RE.match(ln)
                if m:
                    title, p = m.groups()
                    page = int(p)

            if title and page:
                if not self._is_false_positive_toc(sid, title):
                    out.append((sid, title, page))

        return out

    # --------------------------------------------------------------
    # False-positive filter
    # --------------------------------------------------------------
    def _is_false_positive_toc(
        self,
        section_id: Optional[str],
        title: str,
    ) -> bool:
        if not section_id:
            return False

        t = title.lower().strip()

        return t in {
            "version", "version:",
            "release date:",
            "v1.0", "v1.1",
            "v2.0",
            "v3.0", "v3.1", "v3.2",
        }

    # --------------------------------------------------------------
    def _make_entry(
        self,
        sid: str,
        title: str,
        page: int,
    ) -> TocEntry:
        if sid.startswith("FM-"):
            level = 0
            parent = None
            full = title
        else:
            level = sid.count(".") + 1
            parent = self._parent_id(sid)
            full = f"{sid} {title}"

        return TocEntry(
            doc_title=self.doc_title,
            section_id=sid,
            title=title,
            page=page,
            level=level,
            parent_id=parent,
            full_path=full,
            tags=self._infer_tags(title),
        )

    def _parent_id(self, sid: str) -> Optional[str]:
        if "." not in sid:
            return None
        return sid.rsplit(".", 1)[0]

    # --------------------------------------------------------------
    # ✅ CRITICAL FIX: TEMP-safe, appendix-safe sort key
    # --------------------------------------------------------------
    def _sid_key(self, sid: str) -> List[int]:
        # TEMP entries always last
        if sid.startswith("TEMP:"):
            return [9999, 9999]

        # Legacy FM safety
        if sid.startswith("FM-"):
            return [9999]

        key: List[int] = []

        for part in sid.split("."):
            if part.isdigit():
                key.append(int(part))
            elif len(part) == 1 and part.isalpha():
                key.append(ord(part.upper()) - 64)
            else:
                key.append(9999)

        return key

    # --------------------------------------------------------------
    def _infer_tags(self, title: str) -> List[str]:
        t = title.lower()
        tags: List[str] = []

        if any(w in t for w in ["power", "voltage", "current", "vbus"]):
            tags.append("power")

        if any(
            w in t for w in [
                "source", "sink", "device",
                "port", "cable", "plug",
            ]
        ):
            tags.append("device")

        if any(w in t for w in ["state", "transition", "mode"]):
            tags.append("state")

        if any(
            w in t for w in [
                "message", "protocol",
                "sop", "communication",
            ]
        ):
            tags.append("comm")

        return tags
