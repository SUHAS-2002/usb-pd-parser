"""
Chunk extractor for USB PD specification.

Splits extracted PDF text into logical content chunks
based on TOC and internal numeric section headings.

Encapsulation:
- ALL internal state uses name-mangled private attributes (__attr)
- Regex patterns are private class constants
- Access strictly controlled via properties and protected methods
"""

from __future__ import annotations

import re
from typing import Dict, List, Set, Tuple


# ------------------------------------------------------------------
# Chunk Extractor
# ------------------------------------------------------------------
class ChunkExtractor:
    """
    Chunk extractor with maximum encapsulation.

    Uses name mangling for all internal state.
    """

    # --------------------------------------------------------------
    # Private class-level constant (name-mangled)
    # --------------------------------------------------------------
    __SECTION_PATTERN = re.compile(
        r"^(?:\s*)(\d+(?:\.\d+)+)\s+[A-Za-z]",
        re.MULTILINE,
    )

    # --------------------------------------------------------------
    # Controlled access to class constant
    # --------------------------------------------------------------
    @classmethod
    def _get_section_pattern(cls) -> re.Pattern:
        """Get internal section regex pattern (protected)."""
        return cls.__SECTION_PATTERN

    # --------------------------------------------------------------
    # Constructor
    # --------------------------------------------------------------
    def __init__(self) -> None:
        """Initialize chunk extractor with private state."""
        self.__min_page: int | None = None
        self.__max_page: int | None = None
        self.__page_text: Dict[int, str] = {}

        self.__internal_starts: Dict[str, int] = {}
        self.__toc_sorted: List[Dict] = []

        self.__chunks: List[Dict] = []
        self.__mapped_pages: Set[int] = set()

    # --------------------------------------------------------------
    # Read-only properties
    # --------------------------------------------------------------
    @property
    def min_page(self) -> int | None:
        """Minimum page number processed (read-only)."""
        return self.__min_page

    @property
    def max_page(self) -> int | None:
        """Maximum page number processed (read-only)."""
        return self.__max_page

    @property
    def page_text(self) -> Dict[int, str]:
        """Page text mapping (defensive copy)."""
        return self.__page_text.copy()

    @property
    def chunk_count(self) -> int:
        """Number of chunks extracted."""
        return len(self.__chunks)

    # --------------------------------------------------------------
    # Public API
    # --------------------------------------------------------------
    def extract(self, pages: List[Dict], toc: List[Dict]) -> List[Dict]:
        """
        Extract logical chunks from pages using TOC and
        internal numeric section headings.
        """
        if not pages:
            return []

        # Establish page bounds
        self.__min_page, self.__max_page = self._page_bounds(pages)

        # Build page text map
        self.__page_text = self._build_page_text(pages)
        self._fill_missing_pages(
            self.__page_text,
            self.__min_page,
            self.__max_page,
        )

        # Discover internal section starts
        self.__internal_starts = self._find_true_internal_headings(
            self.__page_text
        )

        # Normalize TOC ordering
        self.__toc_sorted = self._sort_toc(toc)

        # Build chunks
        self.__chunks, self.__mapped_pages = self._build_chunks(
            self.__toc_sorted,
            self.__internal_starts,
            self.__page_text,
            self.__min_page,
            self.__max_page,
        )

        # Add fallback chunks for unmapped pages
        self._add_unmapped_pages(
            self.__chunks,
            self.__mapped_pages,
            self.__page_text,
            self.__min_page,
            self.__max_page,
        )

        self.__chunks.sort(key=lambda c: c["page_range"][0])
        return self.__chunks.copy()

    # --------------------------------------------------------------
    # Protected helpers (pipeline internals)
    # --------------------------------------------------------------
    def _find_true_internal_headings(
        self,
        page_text: Dict[int, str],
    ) -> Dict[str, int]:
        """Find numeric internal section headings."""
        found: Dict[str, int] = {}

        for page_num, text in page_text.items():
            for match in self._get_section_pattern().finditer(text):
                section_id = match.group(1)
                if self._is_plausible_section(section_id):
                    found.setdefault(section_id, page_num)

        return found

    def _is_plausible_section(self, section_id: str) -> bool:
        """Validate section ID format."""
        parts = section_id.split(".")
        return 1 < len(parts) <= 5 and all(p.isdigit() for p in parts)

    def _page_bounds(self, pages: List[Dict]) -> Tuple[int, int]:
        page_numbers = [p["page"] for p in pages if "page" in p]
        return min(page_numbers), max(page_numbers)

    def _build_page_text(self, pages: List[Dict]) -> Dict[int, str]:
        return {p["page"]: p.get("text", "") for p in pages}

    def _fill_missing_pages(
        self,
        page_text: Dict[int, str],
        min_page: int,
        max_page: int,
    ) -> None:
        for page in range(min_page, max_page + 1):
            page_text.setdefault(page, "")

    def _sort_toc(self, toc: List[Dict]) -> List[Dict]:
        return sorted(toc, key=lambda x: x.get("page", 0))

    def _build_chunks(
        self,
        toc: List[Dict],
        internal_starts: Dict[str, int],
        page_text: Dict[int, str],
        min_page: int,
        max_page: int,
    ) -> Tuple[List[Dict], Set[int]]:
        chunks: List[Dict] = []
        mapped_pages: Set[int] = set()

        for entry in toc:
            start = entry.get("page")
            if start is None:
                continue

            end = self._next_page(start, toc, max_page)
            content = self._collect_text(page_text, start, end)

            chunks.append(
                {
                    "section_id": entry.get("section_id"),
                    "title": entry.get("title"),
                    "page_range": (start, end),
                    "content": content,
                }
            )

            mapped_pages.update(range(start, end + 1))

        return chunks, mapped_pages

    def _next_page(
        self,
        start: int,
        toc: List[Dict],
        max_page: int,
    ) -> int:
        pages = [e["page"] for e in toc if e.get("page", 0) > start]
        return min(pages) - 1 if pages else max_page

    def _collect_text(
        self,
        page_text: Dict[int, str],
        start: int,
        end: int,
    ) -> str:
        return "\n".join(page_text[p] for p in range(start, end + 1))

    def _add_unmapped_pages(
        self,
        chunks: List[Dict],
        mapped_pages: Set[int],
        page_text: Dict[int, str],
        min_page: int,
        max_page: int,
    ) -> None:
        for page in range(min_page, max_page + 1):
            if page not in mapped_pages:
                chunks.append(
                    {
                        "section_id": None,
                        "title": None,
                        "page_range": (page, page),
                        "content": page_text.get(page, ""),
                    }
                )
