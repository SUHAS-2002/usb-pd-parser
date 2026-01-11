"""
Inline heading extractor (compact OOP, ≤79 chars).

Extracts numeric section headings from document body pages.
These are the authoritative section IDs.
"""

import re
import logging
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
        processed_pages = set()

        for page in pages:
            page_no = page.get("page")
            text = page.get("text", "")

            if not page_no:
                continue

            # IMPORTANT: process page even if text is empty
            if not text:
                text = ""

            for sid, title in self.SECTION_RE.findall(text):
                title_clean = title.strip()

                out.append(
                    {
                        "section_id": sid,
                        "title": title_clean,
                        "page": page_no,
                        "level": sid.count(".") + 1,
                        "parent_id": (
                            sid.rsplit(".", 1)[0]
                            if "." in sid else None
                        ),
                        "full_path": f"{sid} {title_clean}",
                    }
                )

            processed_pages.add(page_no)

        logger = logging.getLogger(__name__)
        logger.info(
            "Processed %d pages for inline heading extraction",
            len(processed_pages),
        )

        return out
