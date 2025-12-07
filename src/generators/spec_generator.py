# src/generators/spec_generator.py

import json
from pathlib import Path
from typing import List, Dict, Any


class SpecJSONLGenerator:
    """
    Builds a unified JSONL specification file containing:
        - A metadata header
        - TOC entries
        - Section content blocks
    Required by assignment.
    """

    # ---------------------------------------------------------
    def generate(
        self,
        toc_path: str,
        chunks_path: str,
        output_path: str = "usb_pd_spec.jsonl"
    ) -> Path:
        """Merge TOC and section content into a single JSONL file."""
        toc_items = self._load_jsonl(Path(toc_path))
        chunks = self._load_jsonl(Path(chunks_path))

        output = Path(output_path)
        with output.open("w", encoding="utf-8") as f:
            header = {
                "type": "metadata",
                "description": "USB PD Specification JSONL"
            }
            f.write(json.dumps(header, ensure_ascii=False) + "\n")

            # Write TOC entries
            for entry in toc_items:
                entry["type"] = "toc_entry"
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")

            # Write content sections
            for section in chunks:
                section["type"] = "content_section"
                f.write(json.dumps(section, ensure_ascii=False) + "\n")

        print(f"Spec JSONL written → {output}")
        return output

    # ---------------------------------------------------------
    def _load_jsonl(self, path: Path) -> List[Dict[str, Any]]:
        """Load items from a JSONL file."""
        items: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))
        return items
