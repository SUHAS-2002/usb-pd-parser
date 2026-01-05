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
        # Intentionally stateless
        pass

    # -----------------------------------------------------------
    # Public API
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
            if not self._is_valid_heading(h):
                continue

            sid = h["section_id"]

            # 🚫 ABSOLUTE RULE: no FM entries
            if self._is_front_matter(sid):
                continue

            out.append(
                self._build_section_record(
                    heading=h,
                    doc_title=doc_title,
                )
            )

        return out

    # -----------------------------------------------------------
    # Internal helpers (encapsulation)
    # -----------------------------------------------------------
    def _is_valid_heading(self, heading: Dict) -> bool:
        """Validate required heading fields."""
        return all(
            heading.get(k)
            for k in ("section_id", "title", "page")
        )

    def _is_front_matter(self, section_id: str) -> bool:
        """Return True if section is front-matter."""
        return section_id.startswith("FM-")

    def _build_section_record(
        self,
        heading: Dict,
        doc_title: str,
    ) -> Dict:
        """Build a single section JSON record."""
        sid: str = heading["section_id"]
        title: str = heading["title"]
        page: int = heading["page"]

        level = sid.count(".") + 1
        parent_id: Optional[str] = (
            sid.rsplit(".", 1)[0] if "." in sid else None
        )

        return {
            "doc_title": doc_title,
            "section_id": sid,
            "title": title,
            "full_path": f"{sid} {title}",
            "page": page,
            "level": level,
            "parent_id": parent_id,
            "tags": [],  # tag inference can be added later
        }
