"""
Inline heading extractor (compact OOP, ≤79 chars).

Extracts numeric section headings from document body pages.
These are the authoritative section IDs.
"""

import re
from typing import List, Dict, Any

from src.core.extractor_base import BaseExtractor


class InlineHeadingExtractor(BaseExtractor):
    """
    Extract numeric section headings from PDF body text.
    """

    SECTION_RE = re.compile(
        r"^\s*(\d+(?:\.\d+)*)\s+(.+)$",
        re.MULTILINE,
    )

    # ----------------------------------------------------------
    def extract(self, pdf_data: Dict[str, Any]) -> List[Dict]:
        pages = pdf_data.get("pages", [])
        out: List[Dict] = []

        for page in pages:
            page_no = page.get("page")
            text = page.get("text", "")

            if not page_no or not text:
                continue

            for sid, title in self.SECTION_RE.findall(text):
                out.append(
                    {
                        "section_id": sid,
                        "title": title.strip(),
                        "page": page_no,
                        "level": sid.count(".") + 1,
                        "parent_id": (
                            sid.rsplit(".", 1)[0]
                            if "." in sid else None
                        ),
                        "full_path": f"{sid} {title.strip()}",
                    }
                )

        return out
