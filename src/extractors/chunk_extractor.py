# src/extractors/chunk_extractor.py

from typing import List, Dict


class ChunkExtractor:
    """
    Given pages and ToC entries, produce complete content chunks.
    Improvements:
      - Guarantees 100% page coverage.
      - Handles gaps between ToC entries.
      - Adds unmapped pages as standalone chunks.
      - Avoids content loss due to missing page_dict entries.
    """

    def extract(self, pages: List[Dict], toc: List[Dict]) -> List[Dict]:
        # Build a fast lookup for text
        page_dict = {p["page_number"]: p.get("text", "") for p in pages}
        last_page = max(page_dict.keys())

        # If no TOC → each page becomes its own chunk (100% coverage)
        if not toc:
            return [
                {
                    "doc_title": "USB Power Delivery Specification",
                    "section_id": f"page-{p['page_number']}",
                    "title": f"Page {p['page_number']}",
                    "full_path": f"Page {p['page_number']}",
                    "page_range": [p["page_number"], p["page_number"]],
                    "content": page_dict.get(p["page_number"], ""),
                    "tags": []
                }
                for p in pages
            ]

        # Sort ToC by page (and section number)
        sorted_toc = sorted(
            toc,
            key=lambda t: (t["page"], tuple(int(x) for x in t["section_id"].split(".")))
        )

        chunks = []
        mapped_pages = set()

        # --- SECTION MAPPING ---
        for idx, entry in enumerate(sorted_toc):
            start = entry["page"]
            end = (
                sorted_toc[idx + 1]["page"] - 1
                if idx + 1 < len(sorted_toc)
                else last_page
            )

            # Clamp boundaries
            if start > last_page:
                start = last_page
            if end < start:
                end = start

            # Collect page text
            texts = []
            for pnum in range(start, end + 1):
                mapped_pages.add(pnum)
                texts.append(page_dict.get(pnum, ""))

            chunks.append({
                "doc_title": entry.get("doc_title", "USB Power Delivery Specification"),
                "section_id": entry["section_id"],
                "title": entry["title"],
                "full_path": entry["full_path"],
                "page_range": [start, end],
                "content": "\n\n".join(texts).strip(),
                "tags": entry.get("tags", []),
            })

        # --- UNMAPPED PAGES (IMPORTANT!) ---
        unmapped = [p for p in page_dict.keys() if p not in mapped_pages]

        for p in sorted(unmapped):
            chunks.append({
                "doc_title": "USB Power Delivery Specification",
                "section_id": f"unmapped-{p}",
                "title": f"Unmapped Page {p}",
                "full_path": f"Unmapped Page {p}",
                "page_range": [p, p],
                "content": page_dict.get(p, ""),
                "tags": [],
            })

        # Final sort by starting page number
        chunks.sort(key=lambda c: c["page_range"][0])

        return chunks
