# src/extractors/toc_extractor.py

import re
from typing import List, Dict


class ToCExtractor:
    """
    A robust ToC extractor that identifies REAL USB-PD section headings.

    Fixes:
    - Rejects dates: "July 2012", "March 2014"
    - Rejects garbage IDs: 23222120, 1024...
    - Rejects decimals from tables: 0.4375
    - Rejects multi-number sequences: "14 13 12 11"
    - Detects only true section patterns like:
        1
        1.1
        1.2.3
        6.5.2.1
    """

    # Pattern: valid section numbering
    VALID_SECTION_RE = re.compile(
        r"^(?P<sid>\d+(?:\.\d+){0,4})\s+(?P<title>[A-Za-z].{2,200})$"
    )

    # Reject titles that are actually dates
    DATE_RE = re.compile(
        r"(January|February|March|April|May|June|July|August|September|October|November|December)",
        re.IGNORECASE
    )

    # Reject text that starts with multiple numbers jammed together
    GARBAGE_NUMBER_RE = re.compile(r"^\d{3,}$")

    def extract(self, pages: List[Dict]) -> List[Dict]:
        toc = []

        for p in pages:
            for raw_line in p["text"].splitlines():
                line = raw_line.strip()

                if not line:
                    continue

                # Try matching valid section pattern
                m = self.VALID_SECTION_RE.match(line)
                if not m:
                    continue

                sid = m.group("sid")
                title = m.group("title").strip()

                # Reject dates
                if self.DATE_RE.search(title):
                    continue

                # Reject garbage numeric strings
                if self.GARBAGE_NUMBER_RE.match(sid):
                    continue

                # Reject decimal garbage (0.4375 etc.)
                if "." in sid:
                    parts = sid.split(".")
                    if any(len(x) > 2 for x in parts):  # 4375 → reject
                        continue

                # Reject headings that are too short
                if len(title) < 3:
                    continue

                toc.append({
                    "doc_title": "USB Power Delivery Specification",
                    "section_id": sid,
                    "title": title,
                    "full_path": f"{sid} {title}",
                    "page": p["page_number"],
                    "level": sid.count(".") + 1,
                    "parent_id": ".".join(sid.split(".")[:-1]) if "." in sid else None,
                    "tags": []
                })

        # Deduplicate by section_id (keep earliest page)
        seen = {}
        for entry in toc:
            sid = entry["section_id"]
            if sid not in seen or entry["page"] < seen[sid]["page"]:
                seen[sid] = entry

        # Sort properly
        def sort_key(e):
            return [int(x) for x in e["section_id"].split(".")]

        return sorted(seen.values(), key=sort_key)
