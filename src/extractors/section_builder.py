"""
Section builder (compact OOP, ≤79 chars).

Builds section-level content blocks from TOC entries and pages.
"""

from typing import List, Dict, Protocol, runtime_checkable


@runtime_checkable
class SectionBuilder(Protocol):
    def build(self, toc: List[Dict], pages: List[Dict]) -> List[Dict]:
        ...


class SectionContentBuilder:
    """
    Concrete section builder strategy.
    """

    def __init__(self) -> None:
        pass

    # ---------------------------------------------------------------
    def _map_pages(self, pages: List[Dict]) -> Dict[int, str]:
        """
        Build a mapping {page_number: text}.
        """
        return {p["page"]: p["text"] for p in pages}

    # ---------------------------------------------------------------
    def _safe_range(
        self,
        toc: List[Dict],
        idx: int,
        max_page: int,
    ) -> List[int]:
        """
        Compute safe page range for a TOC entry.
        """
        start = toc[idx]["page"]

        if idx + 1 < len(toc):
            nxt = toc[idx + 1]["page"]
            end = start if nxt <= start else nxt - 1
        else:
            end = max_page

        return [start, end]

    # ---------------------------------------------------------------
    def build(self, toc: List[Dict], pages: List[Dict]) -> List[Dict]:
        """
        Build structured section blocks.
        """
        if not toc or not pages:
            return []

        page_map = self._map_pages(pages)
        max_page = max(page_map.keys())
        out: List[Dict] = []

        for idx, ent in enumerate(toc):
            start, end = self._safe_range(toc, idx, max_page)

            parts: List[str] = []
            for pg in range(start, end + 1):
                parts.append(page_map.get(pg, ""))

            txt = "\n".join(parts).strip()

            out.append(
                {
                    "doc_title": ent.get(
                        "doc_title",
                        "USB Power Delivery Specification",
                    ),
                    "section_id": ent["section_id"],
                    "title": ent["title"],
                    "full_path": ent["full_path"],
                    "page": start,
                    "page_range": [start, end],
                    "level": ent["level"],
                    "parent_id": ent["parent_id"],
                    "tags": ent.get("tags", []),
                    "text": txt,
                }
            )

        return out
