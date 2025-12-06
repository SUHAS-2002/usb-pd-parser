# src/extractors/toc_extractor.py

import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional


@dataclass
class TocEntry:
    """Single TOC entry for USB PD spec."""
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
    Includes:
      ✓ Multi-column TOC extraction
      ✓ Two-line (ID + title/page) detection
      ✓ Garbage page filtering
      ✓ Off-by-one PDF page correction (CRITICAL FIX)
    """

    DOC_TITLE = "USB Power Delivery Specification"
    MAX_REAL_PAGE = 1100   # PDF actually has 1047 pages

    # Multi-column pattern — extracts SID, title, page
    MULTI_RE = re.compile(
        r"(\d+(?:\.\d+)+)\s+(.+?)\.{3,}\s*(\d{1,4})(?!\S)"
    )

    # ID-only line
    PURE_ID_RE = re.compile(r"^\s*(\d+(?:\.\d+)+)\s*$")

    # Title .................................. 55
    TITLE_LINE_RE = re.compile(r"^\s*(.+?)\.{3,}\s*(\d{1,4})\s*$")

    # ----------------------------------------------------------------------
    def extract(self, pages: List[Dict]) -> List[Dict]:
        raw_entries: List[tuple[str, str, int]] = []

        # Extract TOC matches from all pages
        for page in pages:
            text = page.get("text", "") or ""
            raw_entries.extend(self._extract_from_page(text))

        # Store earliest page for each section_id
        by_id: Dict[str, TocEntry] = {}

        for sid, title, page_num in raw_entries:

            # -------------- CRITICAL FIX -----------------
            # TOC page numbers are 1 page behind actual PDF numbering
            corrected_page = page_num + 1
            # --------------------------------------------

            # Reject obviously invalid pages
            if corrected_page > self.MAX_REAL_PAGE:
                continue

            # Reject invalid section IDs or very short titles
            if not self._plausible(sid, title):
                continue

            # Keep earliest page for each section
            if sid in by_id and corrected_page >= by_id[sid].page:
                continue

            level = sid.count(".") + 1
            parent_id = self._parent_id(sid)
            full_path = f"{sid} {title}"
            tags = self._infer_tags(title)

            by_id[sid] = TocEntry(
                doc_title=self.DOC_TITLE,
                section_id=sid,
                title=title,
                page=corrected_page,
                level=level,
                parent_id=parent_id,
                full_path=full_path,
                tags=tags,
            )

        # Sort TOC entries: first by page, then by section structure
        entries = sorted(
            by_id.values(),
            key=lambda e: (e.page, self._section_key(e.section_id))
        )

        # Fix backward page jumps
        for i in range(1, len(entries)):
            if entries[i].page < entries[i - 1].page:
                entries[i].page = entries[i - 1].page + 1

        return [asdict(e) for e in entries]

    # ----------------------------------------------------------------------
    # Extract from a single page
    # ----------------------------------------------------------------------
    def _extract_from_page(self, text: str) -> List[tuple[str, str, int]]:
        triples: List[tuple[str, str, int]] = []
        lines = text.splitlines()

        # Multi-column TOC extraction
        for line in lines:
            matches = self.MULTI_RE.findall(line)
            for sid, title, page in matches:
                triples.append((sid, title.strip(), int(page)))

        # Two-line ID + title/page detection
        n = len(lines)
        i = 0
        while i < n - 1:
            m_id = self.PURE_ID_RE.match(lines[i].strip())
            if m_id:
                sid = m_id.group(1)
                m_title = self.TITLE_LINE_RE.match(lines[i + 1].strip())
                if m_title:
                    title, page_str = m_title.groups()
                    triples.append((sid, title.strip(), int(page_str)))
                    i += 2
                    continue
            i += 1

        return triples

    # ----------------------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------------------
    def _plausible(self, sid: str, title: str) -> bool:
        """Reject garbage SIDs or invalid titles."""

        parts = sid.split(".")

        # First number must be 1–20 (USB-PD has 11 chapters)
        try:
            top = int(parts[0])
        except ValueError:
            return False

        if not (1 <= top <= 20):
            return False

        # Title must be meaningful
        if len(title) < 3:
            return False

        return True

    def _parent_id(self, sid: str) -> Optional[str]:
        parts = sid.split(".")
        return ".".join(parts[:-1]) if len(parts) > 1 else None

    def _section_key(self, sid: str):
        return [int(x) for x in sid.split(".")]

    def _infer_tags(self, title: str) -> List[str]:
        t = title.lower()
        tags = []
        if any(w in t for w in ["power", "voltage", "current", "vbus"]):
            tags.append("power")
        if any(w in t for w in ["source", "sink", "device", "port", "cable", "plug"]):
            tags.append("device")
        if any(w in t for w in ["state", "transition", "mode"]):
            tags.append("state")
        if any(w in t for w in ["message", "protocol", "sop", "communication"]):
            tags.append("communication")
        if "table" in t:
            tags.append("table")
        return tags
