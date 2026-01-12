# src/generators/metadata_generator.py

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

from src.utils.jsonl_utils import JSONLHandler


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
        output_path: str = "usb_pd_metadata.jsonl",
    ) -> Path:
        """Load TOC + chunks and write a metadata JSON file."""

        toc: List[Dict[str, Any]] = JSONLHandler.load(
            Path(toc_path)
        )
        chunks: List[Dict[str, Any]] = JSONLHandler.load(
            Path(chunks_path)
        )

        coverage = (
            (len(chunks) / len(toc)) * 100
            if toc
            else 0.0
        )

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
            json.dump(
                metadata,
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"Metadata JSON written → {output}")
        return output
