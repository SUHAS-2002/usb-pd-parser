"""
Section builder (compact OOP, ≤79 chars).

Builds usb_pd_spec.jsonl entries exclusively from numeric
inline headings (authoritative source).
"""

from __future__ import annotations

import logging
from typing import List, Dict, Protocol, runtime_checkable

from src.config import CONFIG

_logger = logging.getLogger(__name__)


@runtime_checkable
class SectionBuilder(Protocol):
    def build(
        self,
        toc: List[Dict],
        pages: List[Dict],
        headings: List[Dict],
        doc_title: str,
    ) -> List[Dict]:
        ...


class SectionContentBuilder:
    """
    Authoritative section content builder.

    Encapsulation:
    - Public API: build()
    - ALL internal state uses name-mangled attributes (__attr)
    - Read-only statistics via properties
    - Logic isolated in protected helpers
    """

    # -----------------------------------------------------------
    # Constructor + TRUE PRIVATE state
    # -----------------------------------------------------------
    def __init__(self) -> None:
        self.__max_scan_pages: int = 50

        self.__processed_count: int = 0
        self.__filtered_count: int = 0
        self.__toc_page_count: int = 0

        self.__page_text_map: Dict[int, str] = {}
        self.__sections: List[Dict] = []

    # -----------------------------------------------------------
    # Read-only statistics
    # -----------------------------------------------------------
    @property
    def processed_count(self) -> int:
        return self.__processed_count

    @property
    def filtered_count(self) -> int:
        return self.__filtered_count

    @property
    def toc_page_count(self) -> int:
        return self.__toc_page_count

    # -----------------------------------------------------------
    # Public API
    # -----------------------------------------------------------
    def build(
        self,
        toc: List[Dict],            # interface compatibility
        pages: List[Dict],          # authoritative text source
        headings: List[Dict],       # AUTHORITATIVE
        doc_title: str,
    ) -> List[Dict]:

        # Reset counters
        self.__processed_count = 0
        self.__filtered_count = 0
        self.__toc_page_count = 0

        if not headings or not pages:
            return []

        self.__page_text_map = self._build_page_text_map(pages)
        self.__sections = []

        for idx, heading in enumerate(headings):
            self.__processed_count += 1

            if not self._is_valid_heading(heading):
                self.__filtered_count += 1
                continue

            page = heading["page"]
            sid = heading["section_id"]
            title = heading["title"]

            # Exclude ToC pages
            if CONFIG.pages.TOC_START <= page <= CONFIG.pages.TOC_END:
                self.__toc_page_count += 1
                continue

            # Exclude front matter
            if self._is_front_matter(sid):
                self.__filtered_count += 1
                continue

            # Filter false positives
            if self._is_false_positive(sid, title):
                self.__filtered_count += 1
                continue

            content = self._extract_section_content(
                index=idx,
                headings=headings,
                page_text_map=self.__page_text_map,
            )

            self.__sections.append(
                self._build_section_record(
                    heading=heading,
                    doc_title=doc_title,
                    content=content,
                )
            )

        return self.__sections.copy()

    # -----------------------------------------------------------
    # Heading validation
    # -----------------------------------------------------------
    @staticmethod
    def _is_valid_heading(heading: Dict) -> bool:
        return all(
            heading.get(k)
            for k in ("section_id", "title", "page")
        )

    @staticmethod
    def _is_front_matter(section_id: str) -> bool:
        return section_id.startswith("FM-")

    # -----------------------------------------------------------
    # Page text utilities
    # -----------------------------------------------------------
    def _build_page_text_map(
        self,
        pages: List[Dict],
    ) -> Dict[int, str]:
        page_map: Dict[int, str] = {}

        for page in pages:
            page_no = page.get("page") or page.get("page_number")
            text = page.get("text", "")
            if isinstance(page_no, int) and text:
                page_map[page_no] = text

        return page_map

    # -----------------------------------------------------------
    # Section content extraction
    # -----------------------------------------------------------
    def _extract_section_content(
        self,
        index: int,
        headings: List[Dict],
        page_text_map: Dict[int, str],
    ) -> str:
        start_page = headings[index].get("page", 0)
        if start_page <= 0:
            return ""

        end_page = self._find_end_page(index, headings, start_page)
        parts: List[str] = []

        for page in range(
            start_page,
            min(end_page + 1, start_page + self.__max_scan_pages),
        ):
            raw = page_text_map.get(page)
            if not raw:
                continue

            cleaned = self._clean_page_text(raw)
            if cleaned and len(cleaned) > 20:
                parts.append(cleaned)

        content = "\n\n".join(parts).strip()

        if len(content) < 50:
            _logger.warning(
                "Section %s has low content length (%d chars)",
                headings[index]["section_id"],
                len(content),
            )

        return content

    @staticmethod
    def _find_end_page(
        index: int,
        headings: List[Dict],
        start_page: int,
    ) -> int:
        if index + 1 < len(headings):
            return max(
                start_page,
                headings[index + 1].get("page", start_page) - 1,
            )

        return max(
            (h.get("page", 0) for h in headings),
            default=start_page,
        )

    # -----------------------------------------------------------
    # Text cleanup
    # -----------------------------------------------------------
    def _clean_page_text(self, text: str) -> str:
        lines = text.splitlines()
        cleaned: List[str] = []

        for line in lines:
            line = line.strip()
            if not line:
                continue

            if self._is_header_footer(line):
                continue

            if line.isdigit() and len(line) <= 4:
                continue

            cleaned.append(line)

        return "\n".join(cleaned)

    @staticmethod
    def _is_header_footer(line: str) -> bool:
        lower = line.lower()
        markers = (
            "usb power delivery",
            "table of contents",
            "revision",
            "version",
            "page",
        )
        return any(m in lower for m in markers) and len(line) < 60

    # -----------------------------------------------------------
    # False-positive detection
    # -----------------------------------------------------------
    def _is_false_positive(self, section_id: str, title: str) -> bool:
        title_lower = title.lower().strip()

        if self._is_version_string(title_lower):
            return True

        if self._is_release_date(title_lower):
            return True

        if self._is_date_like(section_id, title_lower):
            return True

        return False

    @staticmethod
    def _is_version_string(title_lower: str) -> bool:
        return title_lower in {
            "version",
            "version:",
            "v1.0",
            "v1.1",
            "v2.0",
            "v3.0",
        }

    @staticmethod
    def _is_release_date(title_lower: str) -> bool:
        if not title_lower.startswith("release date"):
            return False
        return len(title_lower.split()) <= 3

    def _is_date_like(
        self,
        section_id: str,
        title_lower: str,
    ) -> bool:
        if not self._contains_month(title_lower):
            return False

        if section_id.isdigit():
            return True

        if len(section_id) == 1 and section_id.isdigit():
            return True

        if self._is_version_subsection(section_id, title_lower):
            return True

        return False

    @staticmethod
    def _contains_month(title_lower: str) -> bool:
        months = {
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october",
            "november", "december",
        }
        return any(month in title_lower for month in months)

    def _is_version_subsection(
        self,
        section_id: str,
        title_lower: str,
    ) -> bool:
        if section_id.count(".") != 1:
            return False

        major, minor = section_id.split(".", 1)
        if not (major.isdigit() and minor.isdigit()):
            return False

        if title_lower in {
            "1.0", "1.1", "1.2", "1.3", "2.0", "3.0",
        }:
            return True

        return self._contains_month(title_lower)

    # -----------------------------------------------------------
    # Record builder
    # -----------------------------------------------------------
    @staticmethod
    def _build_section_record(
        heading: Dict,
        doc_title: str,
        content: str,
    ) -> Dict:
        sid: str = heading["section_id"]
        title: str = heading["title"]
        page: int = heading["page"]

        return {
            "doc_title": doc_title,
            "section_id": sid,
            "title": title,
            "full_path": f"{sid} {title}",
            "page": page,
            "level": sid.count(".") + 1,
            "parent_id": sid.rsplit(".", 1)[0]
            if "." in sid else None,
            "content": content,
            "tags": [],
        }
