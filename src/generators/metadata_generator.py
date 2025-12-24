# src/generators/metadata_generator.py

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any


class MetadataGenerator:
    """
    Generates a metadata JSON file summarizing:
        - Tool version
        - Timestamp
        - TOC count
        - Section count
        - Coverage percentage
    """

    # -------------------- Private constants -------------------
    __TOOL_VERSION = "1.0.0"

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def generate(
        self,
        toc_path: str,
        chunks_path: str,
        output_path: str = "usb_pd_metadata.jsonl",
    ) -> Path:
        self.__toc_path = Path(toc_path)
        self.__chunks_path = Path(chunks_path)
        self.__output_path = Path(output_path)

        toc = self.__load_jsonl(self.__toc_path)
        chunks = self.__load_jsonl(self.__chunks_path)

        metadata = self.__build_metadata(toc, chunks)
        self.__write_metadata(metadata)

        print(f"Metadata JSON written → {self.__output_path}")
        return self.__output_path

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------
    def __load_jsonl(
        self,
        path: Path,
    ) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []

        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    items.append(json.loads(line))

        return items

    # ---------------------------------------------------------
    def __build_metadata(
        self,
        toc: List[Dict[str, Any]],
        chunks: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        coverage = (
            (len(chunks) / len(toc)) * 100
            if toc else 0.0
        )

        return {
            "type": "metadata",
            "tool_version": self.__TOOL_VERSION,
            "generated_at": datetime.now().isoformat(),
            "toc_count": len(toc),
            "section_count": len(chunks),
            "coverage_percentage": round(coverage, 2),
        }

    # ---------------------------------------------------------
    def __write_metadata(
        self,
        metadata: Dict[str, Any],
    ) -> None:
        with self.__output_path.open(
            "w", encoding="utf-8"
        ) as f:
            json.dump(
                metadata,
                f,
                indent=2,
                ensure_ascii=False,
            )
