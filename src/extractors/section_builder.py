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
    - Filters false positives (dates, versions, metadata)
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
        Filters out false positives (dates, versions, metadata).
        """
        if not headings:
            return []

        out: List[Dict] = []

        for h in headings:
            if not self._is_valid_heading(h):
                continue

            sid = h["section_id"]
            title = h.get("title", "")

            # 🚫 ABSOLUTE RULE: no FM entries
            if self._is_front_matter(sid):
                continue

            # 🚫 Filter false positives
            if self._is_false_positive(sid, title):
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

    def _is_false_positive(self, section_id: str, title: str) -> bool:
        """
        Detect false positive sections (dates, versions, metadata).

        Returns True if section should be filtered out.
        """
        title_lower = title.lower().strip()

        # Filter out version numbers
        if title_lower in [
            "version:", "version", "v1.0", "v1.1",
            "v2.0", "v3.0",
        ]:
            return True

        # Filter out release dates
        if title_lower.startswith("release date"):
            return True

        # Filter out dates (common patterns)
        months = [
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october",
            "november", "december",
        ]
        if any(m in title_lower for m in months):
            if len(title_lower.split()) <= 3:
                return True

        # Numeric section IDs with date-like titles
        if section_id.isdigit() and any(m in title_lower for m in months):
            return True

        # Single-digit numeric IDs with date-like titles
        if len(section_id) == 1 and section_id.isdigit():
            if any(m in title_lower for m in months):
                return True

        # Version-like section IDs (e.g. 1.0, 2.0)
        if section_id.count(".") == 1:
            major, minor = section_id.split(".", 1)
            if major.isdigit() and minor.isdigit():
                if title_lower in [
                    "1.0", "1.1", "1.2", "1.3",
                    "2.0", "3.0",
                ]:
                    return True
                if any(m in title_lower for m in months):
                    return True

        return False

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
            "tags": [],
        }
