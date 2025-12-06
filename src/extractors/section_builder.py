from typing import List, Dict


class SectionContentBuilder:
    """
    Combines TOC entries and extracted pages to produce final
    section-based content blocks, including correct page ranges.
    """

    def build(self, toc: List[Dict], pages: List[Dict]) -> List[Dict]:
        # Map page_number -> text
        page_map = {p["page"]: p["text"] for p in pages}
        sections = []

        for i, entry in enumerate(toc):
            start_page = entry["page"]

            # ---------------------------------------------------------
            # FIXED LOGIC — prevents end_page < start_page (your issue)
            # ---------------------------------------------------------
            if i + 1 < len(toc):
                next_page = toc[i + 1]["page"]

                # If next section starts on SAME page → end_page = start_page
                if next_page <= start_page:
                    end_page = start_page
                else:
                    end_page = next_page - 1
            else:
                end_page = max(page_map.keys())  # last section goes to end
            # ---------------------------------------------------------

            # Combine all pages for this section
            combined_text = []
            for p in range(start_page, end_page + 1):
                combined_text.append(page_map.get(p, ""))

            sections.append({
                "doc_title": entry.get("doc_title", "USB Power Delivery Specification"),
                "section_id": entry["section_id"],
                "title": entry["title"],
                "full_path": entry["full_path"],
                "page": start_page,
                "page_range": [start_page, end_page],   # VALID FOR VALIDATOR
                "level": entry["level"],
                "parent_id": entry["parent_id"],
                "tags": entry.get("tags", []),
                "text": "\n".join(combined_text).strip()
            })

        return sections
