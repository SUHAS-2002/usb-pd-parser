"""
TOC extractor (compact OOP, ≤79 chars).
Extracts TOC entries using regex and plausibility rules.
"""

import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional


@dataclass
class TocEntry:
    doc_title: str
    section_id: str
    title: str
    page: int
    level: int
    parent_id: Optional[str]
    full_path: str
    tags: List[str]


class ToCExtractor:
    """High-coverage TOC extractor for USB-PD PDF."""

    DOC_TITLE = "USB Power Delivery Specification"
    MAX_REAL_PAGE = 1100

    MULTI_RE = re.compile(
        r"(\d+(?:\.\d+)+)\s+(.+?)\.{3,}\s*(\d{1,4})(?!\S)"
    )

    PURE_ID_RE = re.compile(r"^\s*(\d+(?:\.\d+)+)\s*$")

    TITLE_RE = re.compile(
        r"^\s*(.+?)\.{3,}\s*(\d{1,4})\s*$"
    )

    # ---------------------------------------------------------------
    def extract(self, pages: List[Dict]) -> List[Dict]:
        out: List[tuple] = []

        for pg in pages:
            text = pg.get("text", "") or ""
            out.extend(self._from_page(text))

        by_id: Dict[str, TocEntry] = {}

        for sid, title, p in out:
            corr = p + 1
            if corr > self.MAX_REAL_PAGE:
                continue
            if not self._plausible(sid, title):
                continue

            ex = by_id.get(sid)
            if ex and corr >= ex.page:
                continue

            lvl = sid.count(".") + 1
            par = self._parent_id(sid)
            full = f"{sid} {title}"
            tags = self._infer_tags(title)

            by_id[sid] = TocEntry(
                doc_title=self.DOC_TITLE,
                section_id=sid,
                title=title,
                page=corr,
                level=lvl,
                parent_id=par,
                full_path=full,
                tags=tags,
            )

        items = sorted(
            by_id.values(),
            key=lambda e: (e.page, self._sid_key(e.section_id)),
        )

        # Fix backward jumps
        for i in range(1, len(items)):
            if items[i].page < items[i - 1].page:
                items[i].page = items[i - 1].page + 1

        return [asdict(e) for e in items]

    # ---------------------------------------------------------------
    def _from_page(self, text: str) -> List[tuple]:
        triples: List[tuple] = []
        lines = text.splitlines()

        # Single-line patterns
        for ln in lines:
            matches = self.MULTI_RE.findall(ln)
            for sid, title, p in matches:
                triples.append((sid, title.strip(), int(p)))

        # Two-line patterns
        idx = 0
        n = len(lines)

        while idx < n - 1:
            m1 = self.PURE_ID_RE.match(lines[idx].strip())
            if m1:
                sid = m1.group(1)
                nxt = lines[idx + 1].strip()
                m2 = self.TITLE_RE.match(nxt)
                if m2:
                    title, p = m2.groups()
                    triples.append((sid, title.strip(), int(p)))
                    idx += 2
                    continue
            idx += 1

        return triples

    # ---------------------------------------------------------------
    def _plausible(self, sid: str, title: str) -> bool:
        parts = sid.split(".")

        try:
            top = int(parts[0])
        except Exception:
            return False

        if not (1 <= top <= 20):
            return False

        if len(title) < 3:
            return False

        return True

    # ---------------------------------------------------------------
    def _parent_id(self, sid: str) -> Optional[str]:
        parts = sid.split(".")
        if len(parts) > 1:
            return ".".join(parts[:-1])
        return None

    # ---------------------------------------------------------------
    def _sid_key(self, sid: str) -> List[int]:
        return [int(x) for x in sid.split(".")]

    # ---------------------------------------------------------------
    def _infer_tags(self, title: str) -> List[str]:
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
            tags.append("comm")

        if "table" in t:
            tags.append("table")

        return tags
