# src/extractors/toc_extractor.py

import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional


@dataclass
class TocEntry:
    """Single TOC entry for USB PD specification."""
    doc_title: str
    section_id: str
    title: str
    page: int
    level: int
    parent_id: Optional[str]
    full_path: str
    tags: List[str]


class ToCExtractor:
    """
    High-coverage TOC extractor for the USB-PD specification.

    Features:
    - Multi-column layout detection
    - Two-line patterns (SID + title/page)
    - Garbage filtering and plausibility checks
    - Correct TOC → PDF page offset (+1)
    """

    DOC_TITLE = "USB Power Delivery Specification"
    MAX_REAL_PAGE = 1100

    MULTI_RE = re.compile(
        r"(\d+(?:\.\d+)+)\s+(.+?)\.{3,}\s*(\d{1,4})(?!\S)"
    )

    PURE_ID_RE = re.compile(r"^\s*(\d+(?:\.\d+)+)\s*$")

    TITLE_LINE_RE = re.compile(
        r"^\s*(.+?)\.{3,}\s*(\d{1,4})\s*$"
    )

    # ------------------------------------------------------------------
    def extract(self, pages: List[Dict]) -> List[Dict]:
        """Extract TOC entries from all pages."""
        raw_entries: List[tuple] = []

        for page in pages:
            text = page.get("text", "") or ""
            raw_entries.extend(self._extract_from_page(text))

        by_id: Dict[str, TocEntry] = {}

        for sid, title, page_num in raw_entries:
            corrected = page_num + 1

            # Reject impossible pages
            if corrected > self.MAX_REAL_PAGE:
                continue

            if not self._plausible(sid, title):
                continue

            existing = by_id.get(sid)
            if existing and corrected >= existing.page:
                continue

            level = sid.count(".") + 1
            parent = self._parent_id(sid)
            full = f"{sid} {title}"
            tags = self._infer_tags(title)

            by_id[sid] = TocEntry(
                doc_title=self.DOC_TITLE,
                section_id=sid,
                title=title,
                page=corrected,
                level=level,
                parent_id=parent,
                full_path=full,
                tags=tags,
            )

        entries = sorted(
            by_id.values(),
            key=lambda e: (e.page, self._section_key(e.section_id)),
        )

        # Fix backward page jumps
        for i in range(1, len(entries)):
            if entries[i].page < entries[i - 1].page:
                entries[i].page = entries[i - 1].page + 1

        return [asdict(e) for e in entries]

    # ------------------------------------------------------------------
    def _extract_from_page(self, text: str) -> List[tuple]:
        """Extract raw TOC lines from a single page."""
        triples: List[tuple] = []
        lines = text.splitlines()

        for line in lines:
            matches = self.MULTI_RE.findall(line)
            for sid, title, page in matches:
                triples.append((sid, title.strip(), int(page)))

        # Two-line SID → next line title/page
        count = len(lines)
        idx = 0

        while idx < count - 1:
            m_id = self.PURE_ID_RE.match(lines[idx].strip())
            if m_id:
                sid = m_id.group(1)
                nxt = lines[idx + 1].strip()
                m_title = self.TITLE_LINE_RE.match(nxt)
                if m_title:
                    title, page_str = m_title.groups()
                    triples.append((sid, title.strip(), int(page_str)))
                    idx += 2
                    continue
            idx += 1

        return triples

    # ------------------------------------------------------------------
    def _plausible(self, sid: str, title: str) -> bool:
        """Basic sanity checks for TOC entries."""
        parts = sid.split(".")

        try:
            top = int(parts[0])
        except ValueError:
            return False

        if not (1 <= top <= 20):
            return False

        if len(title) < 3:
            return False

        return True

    # ------------------------------------------------------------------
    def _parent_id(self, sid: str) -> Optional[str]:
        """Return parent SID or None."""
        parts = sid.split(".")
        if len(parts) > 1:
            return ".".join(parts[:-1])
        return None

    # ------------------------------------------------------------------
    def _section_key(self, sid: str) -> List[int]:
        """Convert '7.2.10' → [7, 2, 10] for sorting."""
        return [int(x) for x in sid.split(".")]

    # ------------------------------------------------------------------
    def _infer_tags(self, title: str) -> List[str]:
        """Add semantic tags based on title keywords."""
        t = title.lower()
        tags: List[str] = []

        if any(w in t for w in ["power", "voltage", "current", "vbus"]):
            tags.append("power")

        if any(
            w in t for w in [
                "source", "sink", "device", "port", "cable", "plug"
            ]
        ):
            tags.append("device")

        if any(w in t for w in ["state", "transition", "mode"]):
            tags.append("state")

        if any(
            w in t for w in [
                "message", "protocol", "sop", "communication"
            ]
        ):
            tags.append("communication")

        if "table" in t:
            tags.append("table")

        return tags
