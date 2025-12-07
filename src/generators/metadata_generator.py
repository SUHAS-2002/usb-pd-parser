# src/generators/metadata_generator.py

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


class MetadataGenerator:
    """
    Generates a single metadata JSON file summarizing:
        - Tool version
        - Timestamp
        - TOC count
        - Section count
        - Coverage percentage
    """

    TOOL_VERSION = "1.0.0"

    # -------------------------------------------------------------
    def generate(
        self,
        toc_path: str,
        chunks_path: str,
        output_path: str = "usb_pd_metadata.jsonl"
    ) -> Path:
        """Load TOC + chunks and write a metadata JSON file."""
        toc = self._load_jsonl(Path(toc_path))
        chunks = self._load_jsonl(Path(chunks_path))

        coverage = 0.0
        if len(toc) > 0:
            coverage = (len(chunks) / len(toc)) * 100

        metadata = {
            "type": "metadata",
            "tool_version": self.TOOL_VERSION,
            "generated_at": datetime.now().isoformat(),
            "toc_count": len(toc),
            "section_count": len(chunks),
            "coverage_percentage": round(coverage, 2),
        }

        output = Path(output_path)
        with output.open("w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        print(f"Metadata JSON written → {output}")
        return output

    # -------------------------------------------------------------
    def _load_jsonl(self, path: Path) -> List[Dict[str, Any]]:
        """Load a JSONL file into a list of dictionaries."""
        items: List[Dict[str, Any]] = []

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))

        return items
