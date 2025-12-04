# src/extractors/chunk_extractor.py
from typing import List, Dict, Tuple
import math

class ChunkExtractor:
    """
    Given pages and ToC entries, map each ToC entry to a content chunk (page range + text).
    Strategy:
      - Sort ToC by page ascending.
      - For each entry i, range is [page_i, page_{i+1}-1] (last goes to end).
      - Concatenate page texts for the range.
    """

    def extract(self, pages: List[Dict], toc: List[Dict]) -> List[Dict]:
        if not toc:
            # fallback: return each page as a chunk with page number
            return [{
                "section_path": f"Page {p['page_number']}",
                "page_range": [p['page_number'], p['page_number']],
                "content": p['text'][:4000]
            } for p in pages]

        # prepare quick page dict
        page_dict = {p["page_number"]: p["text"] for p in pages}
        last_page = max(page_dict.keys())

        # sort toc by page
        sorted_toc = sorted(toc, key=lambda t: (t["page"], tuple(int(x) for x in t["section_id"].split("."))))
        chunks = []
        for idx, entry in enumerate(sorted_toc):
            start = entry["page"]
            end = sorted_toc[idx + 1]["page"] - 1 if idx + 1 < len(sorted_toc) else last_page
            # clamp
            if start > last_page:
                start = last_page
            if end < start:
                end = start
            # collect text
            texts = []
            for pnum in range(start, end + 1):
                texts.append(page_dict.get(pnum, ""))
            content = "\n\n".join(texts).strip()
            chunks.append({
                "doc_title": entry.get("doc_title"),
                "section_id": entry["section_id"],
                "title": entry["title"],
                "full_path": entry["full_path"],
                "page_range": [start, end],
                "content": content,
                "tags": entry.get("tags", [])
            })
        return chunks
