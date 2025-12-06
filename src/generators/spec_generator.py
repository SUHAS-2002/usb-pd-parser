import json
from pathlib import Path
from typing import List, Dict


class SpecJSONLGenerator:
    """
    Generates a unified spec JSONL file that contains:
        - TOC entries
        - Section content blocks
        - Metadata markers
    Required by assignment.
    """

    def generate(self, toc_path: str, chunks_path: str, output_path: str = "usb_pd_spec.jsonl"):
        toc_path = Path(toc_path)
        chunks_path = Path(chunks_path)
        output_path = Path(output_path)

        toc_entries = self._load_jsonl(toc_path)
        chunks = self._load_jsonl(chunks_path)

        with output_path.open("w", encoding="utf-8") as f:
            # Header metadata (marker)
            f.write(json.dumps({"type": "metadata", "description": "USB PD Specification JSONL"}) + "\n")

            # Write TOC entries
            for entry in toc_entries:
                entry["type"] = "toc_entry"
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

            # Write content sections
            for section in chunks:
                section["type"] = "content_section"
                f.write(json.dumps(section, ensure_ascii=False) + "\n")

        print(f"✅ Spec JSONL written → {output_path}")
        return output_path

    def _load_jsonl(self, path: Path) -> List[Dict]:
        items = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    items.append(json.loads(line))
        return items
