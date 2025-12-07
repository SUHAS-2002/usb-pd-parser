# src/extractors/section_builder.py

from typing import List, Dict


class SectionContentBuilder:
    """
    Build final section-based content blocks from TOC entries
    and extracted pages. Produces accurate page ranges and
    concatenated text for each section.
    """

    def build(self, toc: List[Dict], pages: List[Dict]) -> List[Dict]:
        """
        Assemble sections using TOC page references.

        Parameters
        ----------
        toc : List[Dict]
            Ordered TOC entries with section metadata.
        pages : List[Dict]
            Extracted page text with page numbers.

        Returns
        -------
        List[Dict]
            Section-level structured content blocks.
        """
        page_map = {p["page"]: p["text"] for p in pages}
        sections: List[Dict] = []

        max_page = max(page_map.keys())

        for index, entry in enumerate(toc):
            start_page = entry["page"]

            # Determine end page
            if index + 1 < len(toc):
                next_page = toc[index + 1]["page"]

                # Prevent end_page < start_page (critical fix)
                if next_page <= start_page:
                    end_page = start_page
                else:
                    end_page = next_page - 1
            else:
                end_page = max_page

            # Collect all section pages
            combined = []
            for pg in range(start_page, end_page + 1):
                combined.append(page_map.get(pg, ""))

            text = "\n".join(combined).strip()

            sections.append(
                {
                    "doc_title": entry.get(
                        "doc_title",
                        "USB Power Delivery Specification",
                    ),
                    "section_id": entry["section_id"],
                    "title": entry["title"],
                    "full_path": entry["full_path"],
                    "page": start_page,
                    "page_range": [start_page, end_page],
                    "level": entry["level"],
                    "parent_id": entry["parent_id"],
                    "tags": entry.get("tags", []),
                    "text": text,
                }
            )

        return sections
