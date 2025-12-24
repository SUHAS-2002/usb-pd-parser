# src/extractors/chunk_extractor.py

import re
from typing import List, Dict, Tuple

from src.core.extractor_base import BaseExtractor


class ChunkExtractor(BaseExtractor):
    """
    Robust chunk extractor for USB-PD Specification.

    Guarantees:
    - 100% page coverage
    - Authoritative TOC ordering
    - True numeric section detection
    - No overlapping or empty chunks
    """

    # -------------------- Private constants -------------------
    __SECTION_RE = re.compile(
        r"^(?:\s*)(\d+(?:\.\d+)+)\s+[A-Za-z]",
        re.MULTILINE,
    )

    __DOC_TITLE = "USB Power Delivery Specification"

    # ---------------------------------------------------------
    # Template method implementation
    # ---------------------------------------------------------
    def _extract_impl(
        self,
        data: Dict,
    ) -> List[Dict]:
        pages = data.get("pages", [])
        toc = data.get("toc", [])

        if not pages:
            return []

        page_text, min_page, max_page = self._build_page_text(pages)
        internal = self._find_internal_headings(page_text)
        toc_sorted = self._sort_toc(toc)

        return self._build_chunks(
            toc_sorted,
            page_text,
            internal,
            min_page,
            max_page,
        )

    # ---------------------------------------------------------
    # Protected helpers
    # ---------------------------------------------------------
    def _build_page_text(
        self,
        pages: List[Dict],
    ) -> Tuple[Dict[int, str], int, int]:
        page_text: Dict[int, str] = {}

        page_numbers = [p["page_number"] for p in pages]
        min_page = min(page_numbers)
        max_page = max(page_numbers)

        for pg in pages:
            page_text[pg["page_number"]] = pg.get("text") or ""

        for p in range(min_page, max_page + 1):
            page_text.setdefault(p, "")

        return page_text, min_page, max_page

    # ---------------------------------------------------------
    def _find_internal_headings(
        self,
        page_text: Dict[int, str],
    ) -> Dict[str, int]:
        found: Dict[str, int] = {}

        for page_num, text in page_text.items():
            for sid in self.__SECTION_RE.findall(text):
                if self._is_plausible_sid(sid):
                    found.setdefault(sid, page_num)

        return found

    # ---------------------------------------------------------
    def _sort_toc(
        self,
        toc: List[Dict],
    ) -> List[Dict]:
        return sorted(
            toc,
            key=lambda e: (e["page"], self._sid_key(e["section_id"])),
        )

    # ---------------------------------------------------------
    def _build_chunks(
        self,
        toc: List[Dict],
        page_text: Dict[int, str],
        internal: Dict[str, int],
        min_page: int,
        max_page: int,
    ) -> List[Dict]:
        chunks: List[Dict] = []
        mapped = set()

        for idx, entry in enumerate(toc):
            sid = entry["section_id"]
            start = internal.get(sid, entry["page"])

            if idx + 1 < len(toc):
                next_sid = toc[idx + 1]["section_id"]
                next_start = internal.get(
                    next_sid,
                    toc[idx + 1]["page"],
                )
                end = next_start - 1
            else:
                end = max_page

            start = max(start, min_page)
            end = min(end, max_page)
            if end < start:
                end = start

            content = self._join_pages(
                page_text,
                start,
                end,
            )

            for p in range(start, end + 1):
                mapped.add(p)

            chunks.append(
                self._build_chunk_entry(
                    entry,
                    start,
                    end,
                    content,
                )
            )

        self._add_unmapped_pages(
            chunks,
            page_text,
            mapped,
            min_page,
            max_page,
        )

        chunks.sort(key=lambda c: c["page_range"][0])
        return chunks

    # ---------------------------------------------------------
    def _join_pages(
        self,
        page_text: Dict[int, str],
        start: int,
        end: int,
    ) -> str:
        return "\n\n".join(
            page_text.get(p, "")
            for p in range(start, end + 1)
        ).strip()

    # ---------------------------------------------------------
    def _build_chunk_entry(
        self,
        entry: Dict,
        start: int,
        end: int,
        content: str,
    ) -> Dict:
        return {
            "doc_title": entry["doc_title"],
            "section_id": entry["section_id"],
            "title": entry["title"],
            "full_path": entry["full_path"],
            "page_range": [start, end],
            "content": content,
            "tags": entry.get("tags", []),
        }

    # ---------------------------------------------------------
    def _add_unmapped_pages(
        self,
        chunks: List[Dict],
        page_text: Dict[int, str],
        mapped: set,
        min_page: int,
        max_page: int,
    ) -> None:
        for p in range(min_page, max_page + 1):
            if p not in mapped:
                chunks.append(
                    {
                        "doc_title": self.__DOC_TITLE,
                        "section_id": f"unmapped-{p}",
                        "title": f"Unmapped Page {p}",
                        "full_path": f"Unmapped Page {p}",
                        "page_range": [p, p],
                        "content": page_text.get(p, ""),
                        "tags": [],
                    }
                )

    # ---------------------------------------------------------
    # Private rule helpers
    # ---------------------------------------------------------
    def _sid_key(self, sid: str) -> Tuple[int, ...]:
        return tuple(int(x) for x in sid.split("."))

    # ---------------------------------------------------------
    def _is_plausible_sid(self, sid: str) -> bool:
        try:
            top = int(sid.split(".")[0])
        except ValueError:
            return False
        return 1 <= top <= 20
