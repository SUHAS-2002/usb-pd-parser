# src/extractors/toc_extractor.py
import re
from typing import List, Dict, Optional

KEYWORD_TAGS = {
    "power": ["power", "vbus", "current", "voltage", "negotiat", "contract"],
    "device": ["sink", "source", "drp", "device", "port"],
    "state": ["state", "transition", "transitions", "state machine"],
    "communication": ["message", "request", "communication", "protocol", "sop"],
    "table": ["table"],
    "figure": ["figure", "fig."]
}

class ToCExtractor:
    """
    Extract ToC entries from pages text.
    Strategy:
      - Scan front matter first (pages 1..max_front) for typical ToC lines
      - If not found, scan entire doc for numbered headings
      - Parse lines like: "7.2.5   Zero Negotiated Current........336"
      - Also accept lines like: "7.3 Transitions 339"
    """

    # reasonable range to look for explicit ToC, but fallback searches whole doc
    MAX_FRONT_PAGES = 60

    # pattern matches: id (dots) + title + page_number (at end)
    TOC_LINE_RE = re.compile(
        r'^\s*(\d+(?:\.\d+){0,})\s+(.+?)\s+\.{2,}\s*(\d{1,4})\s*$'  # with dot leaders
        , re.IGNORECASE
    )
    TOC_LINE_RE2 = re.compile(
        r'^\s*(\d+(?:\.\d+){0,})\s+(.+?)\s+(\d{1,4})\s*$'  # simple whitespace-separated
        , re.IGNORECASE
    )

    HEADING_RE = re.compile(r'^\s*(\d+(?:\.\d+){0,})\s+([A-Z0-9].+)$')  # heading at line start

    def extract(self, pages: List[Dict]) -> List[Dict]:
        toc_lines = []

        # 1) Try front matter ToC detection
        front_range = min(len(pages), self.MAX_FRONT_PAGES)
        for i in range(front_range):
            page = pages[i]
            for line in page["text"].splitlines():
                l = line.strip()
                if not l:
                    continue
                m = self.TOC_LINE_RE.match(l) or self.TOC_LINE_RE2.match(l)
                if m:
                    section_id = m.group(1).strip()
                    title = m.group(2).strip().rstrip(".")
                    page_num = int(m.group(3))
                    toc_lines.append((section_id, title, page_num))

        # 2) If none found in front pages, scan entire doc for heading lines
        if not toc_lines:
            for page in pages:
                for line in page["text"].splitlines():
                    l = line.strip()
                    if not l:
                        continue
                    m = self.HEADING_RE.match(l)
                    if m:
                        section_id = m.group(1).strip()
                        title = m.group(2).strip().rstrip(".")
                        toc_lines.append((section_id, title, page["page_number"]))

        # 3) Deduplicate and normalize: prefer earliest occurrence for same id
        toc_map: Dict[str, Dict] = {}
        for sid, title, pg in toc_lines:
            if sid in toc_map:
                # keep smallest page number (earliest)
                if pg < toc_map[sid]["page"]:
                    toc_map[sid]["page"] = pg
                    toc_map[sid]["title"] = title
            else:
                toc_map[sid] = {"section_id": sid, "title": title, "page": pg}

        # 4) Build list sorted by page then by section_id
        toc_list = list(toc_map.values())
        toc_list.sort(key=lambda x: (x["page"], self._section_tuple(x["section_id"])))

        # 5) enrich with level, parent_id, full_path, tags
        enriched = []
        for item in toc_list:
            sid = item["section_id"]
            level = sid.count(".") + 1
            parent_id = None if level == 1 else ".".join(sid.split(".")[:-1])
            full_path = f"{sid} {item['title']}"
            tags = self._infer_tags(item["title"])
            enriched.append({
                "doc_title": "USB Power Delivery Specification",
                "section_id": sid,
                "title": item["title"],
                "full_path": full_path,
                "page": item["page"],
                "level": level,
                "parent_id": parent_id,
                "tags": tags
            })

        return enriched

    @staticmethod
    def _section_tuple(s: str):
        # convert '7.2.10' -> tuple of ints (7,2,10) for correct sorting
        return tuple(int(x) for x in s.split("."))

    @staticmethod
    def _infer_tags(title: str) -> List[str]:
        tl = title.lower()
        tags = set()
        for tag, kwlist in KEYWORD_TAGS.items():
            for kw in kwlist:
                if kw in tl:
                    tags.add(tag)
                    break
        return sorted(tags)
