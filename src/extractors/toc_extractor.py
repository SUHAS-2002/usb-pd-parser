"""
TOC extractor (compact OOP, ≤79 chars).
Extracts TOC entries using regex + structural gating.
Includes front matter, TOC, List of Figures, List of Tables.
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

    # -----------------------------------------------------------
    def extract(self, pages: List[Dict]) -> List[Dict]:
        raw: List[tuple] = []
        in_toc = False
        fm_idx = 0

        for pg in pages:
            text = pg.get("text", "") or ""

            if self.TOC_HEADER_RE.search(text):
                in_toc = True

            if not in_toc:
                continue

            # Stop only when chapter body begins
            for ln in text.splitlines():
                if self.BODY_START_RE.match(ln):
                    in_toc = False
                    break

            if not in_toc:
                break

            clean_lines = []
            for ln in text.splitlines():
                if not self.SELF_REF_RE.match(ln):
                    clean_lines.append(ln)

            for sid, title, p in self._from_page("\n".join(clean_lines)):
                if sid is None:
                    sid = f"FM-{fm_idx}"
                    fm_idx += 1
                raw.append((sid, title, p))

        by_id: Dict[str, TocEntry] = {}

        for sid, title, p in raw:
            if p > self.MAX_REAL_PAGE:
                continue

            if not self._plausible(sid, title):
                continue

            if sid.startswith("FM-"):
                lvl = 0
                par = None
                full = title
            else:
                lvl = sid.count(".") + 1
                par = self._parent_id(sid)
                full = f"{sid} {title}"

            by_id[sid] = TocEntry(
                doc_title=self.DOC_TITLE,
                section_id=sid,
                title=title,
                page=p,
                level=lvl,
                parent_id=par,
                full_path=full,
                tags=self._infer_tags(title),
            )

        items = sorted(
            by_id.values(),
            key=lambda e: (e.page, self._sid_key(e.section_id)),
        )

        return [asdict(e) for e in items]

    # -----------------------------------------------------------
    def _from_page(self, text: str) -> List[tuple]:
        triples: List[tuple] = []

        for ln in text.splitlines():
            for sid, title, p in self.MULTI_RE.findall(ln):
                triples.append((sid, title.strip(), int(p)))

            m = self.FRONT_RE.match(ln)
            if m:
                title, p = m.groups()
                triples.append((None, title.strip(), int(p)))

        return triples

    # -----------------------------------------------------------
    def _plausible(self, sid: str, title: str) -> bool:
        if sid.startswith("FM-"):
            return True

        try:
            top = int(sid.split(".")[0])
        except ValueError:
            return False

        return 1 <= top <= 20 and len(title) >= 3

    # -----------------------------------------------------------
    def _parent_id(self, sid: str) -> Optional[str]:
        parts = sid.split(".")
        return ".".join(parts[:-1]) if len(parts) > 1 else None

    # -----------------------------------------------------------
    def _sid_key(self, sid: str) -> List[int]:
        if sid.startswith("FM-"):
            return [-1, int(sid.split("-")[1])]
        return [int(x) for x in sid.split(".")]

    # -----------------------------------------------------------
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

        if "table" in t:
            tags.append("table")

        return tags
