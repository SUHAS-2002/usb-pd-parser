"""
TOC extractor (compact OOP, ≤79 chars).

Extracts TOC entries and synthesizes numeric section IDs
by aligning TOC pages with body section headings.
"""

import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple

from src.core.extractor_base import BaseExtractor


# ------------------------------------------------------------
# Data model (immutable contract)
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# Extractor
# ------------------------------------------------------------
class ToCExtractor(BaseExtractor):
    """
    Semantic TOC extractor for USB-PD PDF.

    Public API:
        - extract(pages)

    All other methods are protected implementation details.
    """

    # -------------------- Private constants -------------------
    __DOC_TITLE = "USB Power Delivery Specification"
    __MAX_REAL_PAGE = 1100

    __BODY_SECTION_RE = re.compile(
        r"^\s*(\d+(?:\.\d+)*)\s+(.+)$",
        re.MULTILINE,
    )

    __FRONT_RE = re.compile(
        r"^\s*([A-Za-z][A-Za-z\s]+?)\.{3,}\s*(\d{1,4})\s*$"
    )

    __TOC_HEADER_RE = re.compile(
        r"\btable\s+of\s+contents\b",
        re.IGNORECASE,
    )

    __BODY_START_RE = re.compile(
        r"^\s*1\s+Introduction\b",
        re.IGNORECASE,
    )

    __SELF_REF_RE = re.compile(
        r"^\s*table\s+of\s+contents\s*\.{3,}",
        re.IGNORECASE,
    )

    # ---------------------------------------------------------
    # Template method implementation
    # ---------------------------------------------------------
    def _extract_impl(self, pages: List[Dict]) -> List[Dict]:
        toc_raw = self._extract_raw_toc(pages)
        page_to_section = self._build_page_section_map(pages)
        entries = self._promote_entries(toc_raw, page_to_section)

        items = sorted(
            entries.values(),
            key=lambda e: (e.page, self._sid_key(e.section_id)),
        )

        return [asdict(e) for e in items]

    # ---------------------------------------------------------
    # Protected helpers
    # ---------------------------------------------------------
    def _extract_raw_toc(
        self,
        pages: List[Dict],
    ) -> List[Tuple[str, str, int]]:
        """
        Extract unnumbered TOC entries from front matter.
        """
        toc_raw: List[Tuple[str, str, int]] = []
        in_toc = False
        fm_idx = 0

        for pg in pages:
            text = pg.get("text", "") or ""

            if self.__TOC_HEADER_RE.search(text):
                in_toc = True

            if not in_toc:
                continue

            for ln in text.splitlines():
                if self.__BODY_START_RE.match(ln):
                    in_toc = False
                    break

            if not in_toc:
                break

            lines = [
                ln for ln in text.splitlines()
                if not self.__SELF_REF_RE.match(ln)
            ]

            for title, page in self._parse_front_lines(
                "\n".join(lines)
            ):
                sid = f"FM-{fm_idx}"
                fm_idx += 1
                toc_raw.append((sid, title, page))

        return toc_raw

    # ---------------------------------------------------------
    def _parse_front_lines(
        self,
        text: str,
    ) -> List[Tuple[str, int]]:
        """
        Parse TOC front-matter lines.
        """
        out: List[Tuple[str, int]] = []

        for ln in text.splitlines():
            m = self.__FRONT_RE.match(ln)
            if m:
                title, page = m.groups()
                out.append((title.strip(), int(page)))

        return out

    # ---------------------------------------------------------
    def _build_page_section_map(
        self,
        pages: List[Dict],
    ) -> Dict[int, str]:
        """
        Map page number → first numeric section ID.
        """
        mapping: Dict[int, str] = {}

        for p in pages:
            m = self.__BODY_SECTION_RE.search(
                p.get("text", "")
            )
            if m:
                mapping[p["page"]] = m.group(1)

        return mapping

    # ---------------------------------------------------------
    def _promote_entries(
        self,
        toc_raw: List[Tuple[str, str, int]],
        page_to_section: Dict[int, str],
    ) -> Dict[str, TocEntry]:
        """
        Promote FM-* IDs to real numeric section IDs.
        """
        entries: Dict[str, TocEntry] = {}

        for sid, title, page in toc_raw:
            if page > self.__MAX_REAL_PAGE:
                continue

            real_sid = self._find_real_section(
                page,
                page_to_section,
            ) or sid

            if real_sid.startswith("FM-"):
                level = 0
                parent = None
                full = title
            else:
                level = real_sid.count(".") + 1
                parent = self._parent_id(real_sid)
                full = f"{real_sid} {title}"

            entries[real_sid] = TocEntry(
                doc_title=self.__DOC_TITLE,
                section_id=real_sid,
                title=title,
                page=page,
                level=level,
                parent_id=parent,
                full_path=full,
                tags=self._infer_tags(title),
            )

        return entries

    # ---------------------------------------------------------
    def _find_real_section(
        self,
        page: int,
        page_to_section: Dict[int, str],
    ) -> Optional[str]:
        for p in range(page, page + 6):
            if p in page_to_section:
                return page_to_section[p]
        return None

    # ---------------------------------------------------------
    def _parent_id(self, sid: str) -> Optional[str]:
        if "." not in sid:
            return None
        return sid.rsplit(".", 1)[0]

    # ---------------------------------------------------------
    def _sid_key(self, sid: str) -> List[int]:
        if sid.startswith("FM-"):
            return [9999]
        return [int(x) for x in sid.split(".")]

    # ---------------------------------------------------------
    def _infer_tags(self, title: str) -> List[str]:
        t = title.lower()
        tags: List[str] = []

        if any(w in t for w in ("power", "voltage", "current", "vbus")):
            tags.append("power")

        if any(
            w in t
            for w in (
                "source",
                "sink",
                "device",
                "port",
                "cable",
                "plug",
            )
        ):
            tags.append("device")

        if any(w in t for w in ("state", "transition", "mode")):
            tags.append("state")

        if any(
            w in t
            for w in (
                "message",
                "protocol",
                "sop",
                "communication",
            )
        ):
            tags.append("comm")

        return tags
