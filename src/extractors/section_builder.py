"""
Section builder (compact OOP, ≤79 chars).

Builds usb_pd_spec.jsonl entries exclusively from numeric
inline headings (authoritative source).
"""

from typing import List, Dict, Protocol, runtime_checkable, Optional


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

    RULES:
    - Uses ONLY numeric inline headings
    - Ignores FM-* completely
    - Produces manager-approved JSONL format
    """

    def __init__(self) -> None:
        pass

    # -----------------------------------------------------------
    def build(
        self,
        toc: List[Dict],            # kept for interface compatibility
        pages: List[Dict],          # future use (content slicing)
        headings: List[Dict],       # AUTHORITATIVE
        doc_title: str,
    ) -> List[Dict]:
        """
        Build spec sections from numeric inline headings.
        """
        if not headings:
            return []

        out: List[Dict] = []

        for h in headings:
            sid = h.get("section_id")
            title = h.get("title")
            page = h.get("page")

            if not sid or not title or not page:
                continue

            # 🚫 ABSOLUTE RULE: no FM entries in spec output
            if sid.startswith("FM-"):
                continue

            level = sid.count(".") + 1
            parent_id: Optional[str] = (
                sid.rsplit(".", 1)[0] if "." in sid else None
            )

            out.append(
                {
                    "doc_title": doc_title,
                    "section_id": sid,
                    "title": title,
                    "full_path": f"{sid} {title}",
                    "page": page,
                    "level": level,
                    "parent_id": parent_id,
                    "tags": [],  # tag inference can be added later
                }
            )

        return out
