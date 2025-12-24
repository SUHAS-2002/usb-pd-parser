"""
Section builder (compact OOP, ≤79 chars).

Builds usb_pd_spec.jsonl entries exclusively from numeric
inline headings (authoritative source).
"""

from typing import List, Dict, Protocol, runtime_checkable, Optional


# ------------------------------------------------------------
# Public interface (stable contract)
# ------------------------------------------------------------
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


# ------------------------------------------------------------
# Concrete implementation
# ------------------------------------------------------------
class SectionContentBuilder:
    """
    Authoritative section content builder.

    Encapsulation rules:
    - build() is the ONLY public method
    - all validation and rules are private/protected
    - FM-* sections are strictly forbidden
    """

    # --------------------------------------------------------
    # Public API
    # --------------------------------------------------------
    def build(
        self,
        toc: List[Dict],            # interface compatibility
        pages: List[Dict],          # future slicing support
        headings: List[Dict],       # AUTHORITATIVE
        doc_title: str,
    ) -> List[Dict]:
        if not headings:
            return []

        return self._build_from_headings(
            headings,
            doc_title,
        )

    # --------------------------------------------------------
    # Protected helpers
    # --------------------------------------------------------
    def _build_from_headings(
        self,
        headings: List[Dict],
        doc_title: str,
    ) -> List[Dict]:
        """
        Build section entries from validated headings.
        """
        out: List[Dict] = []

        for heading in headings:
            if not self.__is_valid_heading(heading):
                continue

            entry = self._build_section_entry(
                heading,
                doc_title,
            )

            if entry:
                out.append(entry)

        return out

    # --------------------------------------------------------
    def _build_section_entry(
        self,
        heading: Dict,
        doc_title: str,
    ) -> Optional[Dict]:
        """
        Construct a single JSONL section entry.
        """
        sid = heading["section_id"]
        title = heading["title"]
        page = heading["page"]

        level = sid.count(".") + 1
        parent_id = self._parent_id(sid)

        return {
            "doc_title": doc_title,
            "section_id": sid,
            "title": title,
            "full_path": f"{sid} {title}",
            "page": page,
            "level": level,
            "parent_id": parent_id,
            "tags": [],  # reserved for future inference
        }

    # --------------------------------------------------------
    def _parent_id(self, sid: str) -> Optional[str]:
        if "." not in sid:
            return None
        return sid.rsplit(".", 1)[0]

    # --------------------------------------------------------
    # Private rule enforcement
    # --------------------------------------------------------
    def __is_valid_heading(self, heading: Dict) -> bool:
        """
        Enforce authoritative section rules.
        """
        sid = heading.get("section_id")
        title = heading.get("title")
        page = heading.get("page")

        if not sid or not title or not page:
            return False

        # 🚫 Absolute rule: no FM sections allowed
        if sid.startswith("FM-"):
            return False

        return True
