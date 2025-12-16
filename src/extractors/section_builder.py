"""
Section builder (compact OOP, ≤79 chars).

Builds clean section-level content blocks from TOC and pages.
"""

from typing import List, Dict, Protocol, runtime_checkable


@runtime_checkable
class SectionBuilder(Protocol):
    def build(self, toc: List[Dict], pages: List[Dict]) -> List[Dict]:
        ...


class SectionContentBuilder:
    """
    Robust section content builder.
    """

    def __init__(self) -> None:
        pass

    # ---------------------------------------------------------------
    def _map_pages(self, pages: List[Dict]) -> Dict[int, str]:
        """Build a mapping {page_number: text}."""
        return {
            p["page"]: p.get("text", "")
            for p in pages
            if "page" in p
        }

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
            end = nxt - 1 if nxt > start else start
        else:
            end = max_page

        return [start, end]

    # ---------------------------------------------------------------
    def build(self, toc: List[Dict], pages: List[Dict]) -> List[Dict]:
        """
        Build structured section content blocks.
        """
        if not toc or not pages:
            return []

        page_map = self._map_pages(pages)
        max_page = max(page_map.keys())
        out: List[Dict] = []

        # Detect TOC page range to exclude it
        toc_pages = {
            e["page"]
            for e in toc
            if isinstance(e.get("section_id"), str)
            and e["section_id"].startswith("FM-")
        }

        for idx, ent in enumerate(toc):
            sid = ent["section_id"]
            start, end = self._safe_range(toc, idx, max_page)

            parts: List[str] = []

            for pg in range(start, end + 1):
                # Skip TOC navigation pages
                if pg in toc_pages and not sid.startswith("FM-"):
                    continue

                parts.append(page_map.get(pg, ""))

            text = "\n".join(parts).strip()

            # Skip empty sections (except front-matter)
            if not text and not sid.startswith("FM-"):
                continue

            out.append(
                {
                    "doc_title": ent.get(
                        "doc_title",
                        "USB Power Delivery Specification",
                    ),
                    "section_id": sid,
                    "title": ent["title"],
                    "full_path": ent["full_path"],
                    "page": start,
                    "page_range": [start, end],
                    "level": ent["level"],
                    "parent_id": ent["parent_id"],
                    "tags": ent.get("tags", []),
                    "text": text,
                }
            )

        return out
