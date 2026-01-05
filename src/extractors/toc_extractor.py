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

    # --------------------------------------------------------------
    # Polymorphism (special methods)
    # --------------------------------------------------------------
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"{self.section_id}: {self.title} (page {self.page})"

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return (
            "TocEntry("
            f"section_id={self.section_id!r}, "
            f"page={self.page}, level={self.level}"
            ")"
        )

    def __len__(self) -> int:
        """Return the length of the title."""
        return len(self.title)

    def __eq__(self, other: object) -> bool:
        """Logical equality comparison."""
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

    TOC_HEADER_RE = re.compile(
        r"\btable\s+of\s+contents\b",
        re.IGNORECASE,
    )

    BODY_START_RE = re.compile(
        r"^\s*1\s+Introduction\b",
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

    # --------------------------------------------------------------
    # Properties (Encapsulation)
    # --------------------------------------------------------------
    @property
    def doc_title(self) -> str:
        return self._doc_title

    @property
    def max_real_page(self) -> int:
        return self._max_real_page

    # --------------------------------------------------------------
    # Public API (unchanged)
    # --------------------------------------------------------------
    def extract(self, pages: List[Dict]) -> List[Dict]:
        toc_raw: List[Tuple[str, str, int]] = []
        in_toc = False
        fm_idx = 0

        for pg in pages:
            text = pg.get("text", "") or ""

            if self.TOC_HEADER_RE.search(text):
                in_toc = True

            if not in_toc:
                continue

            for ln in text.splitlines():
                if self.BODY_START_RE.match(ln):
                    in_toc = False
                    break

            if not in_toc:
                break

            lines = [
                ln for ln in text.splitlines()
                if not self.SELF_REF_RE.match(ln)
            ]

            for title, p in self._from_page("\n".join(lines)):
                sid = f"FM-{fm_idx}"
                fm_idx += 1
                toc_raw.append((sid, title, p))

        page_to_section = self._build_page_section_map(pages)
        entries: Dict[str, TocEntry] = {}

        for sid, title, page in toc_raw:
            if page > self.max_real_page:
                continue

            real_sid = self._promote(page, page_to_section) or sid

            if real_sid.startswith("FM-"):
                level = 0
                parent = None
                full = title
            else:
                level = real_sid.count(".") + 1
                parent = self._parent_id(real_sid)
                full = f"{real_sid} {title}"

            entries[real_sid] = TocEntry(
                doc_title=self.doc_title,
                section_id=real_sid,
                title=title,
                page=page,
                level=level,
                parent_id=parent,
                full_path=full,
                tags=self._infer_tags(title),
            )

        items = sorted(
            entries.values(),
            key=lambda e: (e.page, self._sid_key(e.section_id)),
        )

        return [asdict(e) for e in items]

    # --------------------------------------------------------------
    # Internals
    # --------------------------------------------------------------
    def _from_page(self, text: str) -> List[Tuple[str, int]]:
        out: List[Tuple[str, int]] = []

        for ln in text.splitlines():
            m = self.FRONT_RE.match(ln)
            if m:
                title, p = m.groups()
                out.append((title.strip(), int(p)))

        return out

    def _build_page_section_map(
        self,
        pages: List[Dict],
    ) -> Dict[int, str]:
        mapping: Dict[int, str] = {}

        for p in pages:
            text = p.get("text", "")
            m = self.BODY_SECTION_RE.search(text)
            if m:
                mapping[p["page"]] = m.group(1)

        return mapping

    def _promote(
        self,
        page: int,
        page_to_section: Dict[int, str],
    ) -> Optional[str]:
        for p in range(page, page + 6):
            if p in page_to_section:
                return page_to_section[p]
        return None

    def _parent_id(self, sid: str) -> Optional[str]:
        if "." not in sid:
            return None
        return sid.rsplit(".", 1)[0]

    def _sid_key(self, sid: str) -> List[int]:
        if sid.startswith("FM-"):
            return [9999]
        return [int(x) for x in sid.split(".")]

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
