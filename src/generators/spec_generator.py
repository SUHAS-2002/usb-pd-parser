# src/generators/spec_generator.py

import json
from pathlib import Path
from typing import List, Dict, Any

from src.utils.jsonl_utils import JSONLHandler


class SpecJSONLGenerator:
    """
    Builds the final USB PD specification JSONL file.

    IMPORTANT:
    - Writes ONLY content sections
    - No metadata header
    - No TOC duplication
    - No artificial 'type' field
    """

    # ---------------------------------------------------------
    def generate(
        self,
        toc_path: str,          # kept for interface compatibility
        chunks_path: str,
        output_path: str = "usb_pd_spec.jsonl",
    ) -> Path:
        """
        Generate JSONL file with only content sections.
        """
        # NOTE: toc_path intentionally unused (STEP 1 requirement)

        chunks: List[Dict[str, Any]] = JSONLHandler.load(
            Path(chunks_path)
        )

        output = Path(output_path)
        with output.open("w", encoding="utf-8") as f:
            for section in chunks:
                clean_section = {
                    key: value
                    for key, value in section.items()
                    if key != "type"
                }
                f.write(
                    json.dumps(
                        clean_section,
                        ensure_ascii=False,
                    )
                    + "\n"
                )

        print(f"Spec JSONL written → {output}")
        return output
