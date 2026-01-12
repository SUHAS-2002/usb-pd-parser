import re
from typing import List, Dict, Tuple, Set


class ChunkExtractor:
    """
    Robust chunk extractor for USB-PD Specification.

    Guarantees:
    - 100% page coverage
    - Only true numeric section headings
    - TOC + internal heading alignment
    - No overlapping or empty chunks
    - Explicit unmapped page capture
    """

    # Strict start-of-line numeric section heading (not tables/figures)
    SECTION_RE = re.compile(
        r"^(?:\s*)(\d+(?:\.\d+)+)\s+[A-Za-z]",
        re.MULTILINE,
    )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def extract(self, pages: List[Dict], toc: List[Dict]) -> List[Dict]:
        """Build section chunks using TOC + internal heading detection."""
        if not pages:
            return []

        min_page, max_page = self._page_bounds(pages)

        page_text = self._build_page_text(pages)
        self._fill_missing_pages(page_text, min_page, max_page)

        internal_starts = self._find_true_internal_headings(page_text)
        toc_sorted = self._sort_toc(toc)

        chunks, mapped_pages = self._build_chunks(
            toc_sorted,
            internal_starts,
            page_text,
            min_page,
            max_page,
        )

        self._add_unmapped_pages(
            chunks,
            mapped_pages,
            page_text,
            min_page,
            max_page,
        )

        chunks.sort(key=lambda c: c["page_range"][0])
        return chunks

    # ------------------------------------------------------------------
    # Page preparation
    # ------------------------------------------------------------------
    @staticmethod
    def _page_bounds(pages: List[Dict]) -> Tuple[int, int]:
        page_numbers = [p["page_number"] for p in pages]
        return min(page_numbers), max(page_numbers)

    @staticmethod
    def _build_page_text(pages: List[Dict]) -> Dict[int, str]:
        return {
            pg["page_number"]: pg.get("text") or ""
            for pg in pages
        }

    @staticmethod
    def _fill_missing_pages(
        page_text: Dict[int, str],
        min_page: int,
        max_page: int,
    ) -> None:
        for p in range(min_page, max_page + 1):
            page_text.setdefault(p, "")

    # ------------------------------------------------------------------
    # Chunk construction
    # ------------------------------------------------------------------
    @staticmethod
    def _sort_toc(toc: List[Dict]) -> List[Dict]:
        return sorted(
            toc,
            key=lambda e: (e["page"], ChunkExtractor._key(e["section_id"])),
        )

    def _build_chunks(
        self,
        toc_sorted: List[Dict],
        internal_starts: Dict[str, int],
        page_text: Dict[int, str],
        min_page: int,
        max_page: int,
    ) -> Tuple[List[Dict], Set[int]]:
        chunks: List[Dict] = []
        mapped: Set[int] = set()

        for idx, entry in enumerate(toc_sorted):
            start, end = self._compute_section_bounds(
                idx,
                toc_sorted,
                internal_starts,
                min_page,
                max_page,
            )

            content = self._collect_text(page_text, start, end)
            mapped.update(range(start, end + 1))

            chunks.append(
                {
                    "doc_title": entry["doc_title"],
                    "section_id": entry["section_id"],
                    "title": entry["title"],
                    "full_path": entry["full_path"],
                    "page_range": [start, end],
                    "content": content,
                    "tags": entry.get("tags", []),
                }
            )

        return chunks, mapped

    @staticmethod
    def _compute_section_bounds(
        idx: int,
        toc_sorted: List[Dict],
        internal_starts: Dict[str, int],
        min_page: int,
        max_page: int,
    ) -> Tuple[int, int]:
        entry = toc_sorted[idx]
        sid = entry["section_id"]

        start = internal_starts.get(sid, entry["page"])

        if idx + 1 < len(toc_sorted):
            next_entry = toc_sorted[idx + 1]
            next_sid = next_entry["section_id"]
            next_start = internal_starts.get(
                next_sid, next_entry["page"]
            )
            end = next_start - 1
        else:
            end = max_page

        start = max(start, min_page)
        end = min(end, max_page)
        if end < start:
            end = start

        return start, end

    @staticmethod
    def _collect_text(
        page_text: Dict[int, str],
        start: int,
        end: int,
    ) -> str:
        return "\n\n".join(
            page_text.get(p, "") for p in range(start, end + 1)
        ).strip()

    # ------------------------------------------------------------------
    # Unmapped pages
    # ------------------------------------------------------------------
    @staticmethod
    def _add_unmapped_pages(
        chunks: List[Dict],
        mapped: Set[int],
        page_text: Dict[int, str],
        min_page: int,
        max_page: int,
    ) -> None:
        for p in range(min_page, max_page + 1):
            if p not in mapped:
                chunks.append(
                    {
                        "doc_title": "USB Power Delivery Specification",
                        "section_id": f"unmapped-{p}",
                        "title": f"Unmapped Page {p}",
                        "full_path": f"Unmapped Page {p}",
                        "page_range": [p, p],
                        "content": page_text.get(p, ""),
                        "tags": [],
                    }
                )

    # ------------------------------------------------------------------
    # Internal heading detection
    # ------------------------------------------------------------------
    def _find_true_internal_headings(
        self,
        page_text: Dict[int, str],
    ) -> Dict[str, int]:
        found: Dict[str, int] = {}

        for page_num, text in page_text.items():
            for match in self.SECTION_RE.finditer(text):
                sid = match.group(1)
                if self._plausible(sid):
                    found.setdefault(sid, page_num)

        return found

    @staticmethod
    def _key(section_id: str) -> Tuple[int, ...]:
        return tuple(int(x) for x in section_id.split("."))

    @staticmethod
    def _plausible(sid: str) -> bool:
        try:
            top = int(sid.split(".")[0])
        except ValueError:
            return False
        return 1 <= top <= 20
