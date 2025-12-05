# src/extractors/toc_extractor.py

import re
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional


@dataclass
class TocEntry:
    """Single Table-of-Contents entry."""
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
    Robust ToC extractor for USB PD specification.

    - Uses numbered heading patterns (1, 1.1, 1.2.3, etc.).
    - Scans *all* pages (not just first 60).
    - Filters out:
        * pure numeric garbage (e.g., 23222120)
        * table bitfields (0.4375, 1024...)
        * date-like headings ("May 2015", "June 2018")
    - Infers:
        * level = number of dots + 1
        * parent_id from section_id
        * full_path = "{section_id} {title}"
    - Returns list[dict] so it plugs into existing pipeline.
    """

    # Heading: "2 Title", "2.1 Something", "3.4.1 Foo Bar"
    HEADING_RE = re.compile(
        r"^\s*(\d+(?:\.\d+){0,4})\s+([A-Za-z][^\n]+?)\s*$"
    )

    # Pure big integers (likely bitfield tables, not section IDs)
    PURE_INT_RE = re.compile(r"^\d{3,}$")

    # Weird decimal-like (0.4375 etc) from tables
    DECIMALISH_RE = re.compile(r"^\d+\.\d{2,}$")

    # Month words – used to filter out date-like stuff
    MONTH_WORDS = [
        "january", "february", "march", "april", "may",
        "june", "july", "august", "september",
        "october", "november", "december",
    ]

    DOC_TITLE = "USB Power Delivery Specification"

    def extract(self, pages: List[Dict]) -> List[Dict]:
        """
        Main public API: takes list of pages:
            [{"page_number": int, "text": str}, ...]
        Returns list of dicts (JSON-serializable) representing ToC entries.
        """
        entries: List[TocEntry] = []
        seen_ids = set()

        for page in pages:
            page_num = page["page_number"]
            text = page.get("text", "") or ""

            for raw_line in text.splitlines():
                line = raw_line.strip()
                if not line:
                    continue

                match = self.HEADING_RE.match(line)
                if not match:
                    continue

                section_id = match.group(1).strip()
                title = match.group(2).strip().rstrip(".")

                if not self._is_plausible_section_id(section_id):
                    continue
                if not self._is_plausible_title(title):
                    continue

                if section_id in seen_ids:
                    # keep first occurrence (earliest page)
                    continue
                seen_ids.add(section_id)

                level = section_id.count(".") + 1
                parent_id = self._parent_id(section_id)
                full_path = f"{section_id} {title}"
                tags = self._infer_tags(title)

                entry = TocEntry(
                    doc_title=self.DOC_TITLE,
                    section_id=section_id,
                    title=title,
                    page=page_num,
                    level=level,
                    parent_id=parent_id,
                    full_path=full_path,
                    tags=tags,
                )
                entries.append(entry)

        # stable sort: first by page, then by numeric section_id
        entries.sort(
            key=lambda e: (e.page, self._section_tuple(e.section_id))
        )

        # Convert dataclasses → dicts so existing pipeline continues to work
        return [asdict(e) for e in entries]

    # ------------------------------------------------------------------ #
    # Helper methods – make the logic testable & OOP-friendly
    # ------------------------------------------------------------------ #

    @staticmethod
    def _section_tuple(section_id: str):
        """Convert '7.2.10' -> (7, 2, 10) for numeric sort."""
        return tuple(int(p) for p in section_id.split("."))

    @classmethod
    def _parent_id(cls, section_id: str) -> Optional[str]:
        parts = section_id.split(".")
        return ".".join(parts[:-1]) if len(parts) > 1 else None

    @classmethod
    def _is_plausible_section_id(cls, section_id: str) -> bool:
        """
        Filter out IDs that we know are junk for USB PD spec:
        - Very large top-level numbers (> 50)
        - Pure long integers (e.g. "23222120")
        - Decimal-like values with many digits ("0.4375")
        """
        # '23222120'
        if cls.PURE_INT_RE.match(section_id):
            return False

        # '0.4375' or '1024.000'
        if cls.DECIMALISH_RE.match(section_id):
            return False

        # Top-level like "1024" or "99" are unlikely as chapter numbers
        if "." not in section_id:
            try:
                top = int(section_id)
                if top > 50:
                    return False
            except ValueError:
                return False

        return True

    @classmethod
    def _is_plausible_title(cls, title: str) -> bool:
        """
        Filter out date-like titles and numeric garbage.
        """
        t = title.lower()

        # Filter date-like lines: "July, 2012", "May 2015", etc.
        for m in cls.MONTH_WORDS:
            if m in t:
                # e.g. "July, 2012", "May 2015"
                # these are revision history lines, not section headings
                return False

        # Title must start with a letter; heading regex already enforces that
        return True

    @staticmethod
    def _infer_tags(title: str) -> List[str]:
        """
        Very simple keyword-based tags. You can expand this later.
        """
        tl = title.lower()
        tags = []

        if any(k in tl for k in ["power", "voltage", "current", "vbus"]):
            tags.append("power")
        if any(k in tl for k in ["sink", "source", "device", "drp", "port"]):
            tags.append("device")
        if any(k in tl for k in ["state", "transition", "mode"]):
            tags.append("state")
        if any(k in tl for k in ["message", "protocol", "communication", "sop"]):
            tags.append("communication")
        if any(k in tl for k in ["table"]):
            tags.append("table")
        if any(k in tl for k in ["figure", "fig."]):
            tags.append("figure")

        return tags
