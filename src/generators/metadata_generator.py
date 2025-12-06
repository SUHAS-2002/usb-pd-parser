import json
from pathlib import Path
from datetime import datetime


class MetadataGenerator:
    """
    Generates metadata JSONL containing:
        - PDF name
        - Total pages extracted
        - TOC entry count
        - Section count
        - Timestamp
        - Tool version
        - Coverage % (TOC vs chunks)
    """

    TOOL_VERSION = "1.0.0"

    def generate(self, toc_path: str, chunks_path: str, output_path: str = "usb_pd_metadata.jsonl"):
        toc_path = Path(toc_path)
        chunks_path = Path(chunks_path)
        output_path = Path(output_path)

        toc = self._load_jsonl(toc_path)
        chunks = self._load_jsonl(chunks_path)

        metadata = {
            "type": "metadata",
            "tool_version": self.TOOL_VERSION,
            "generated_at": datetime.now().isoformat(),
            "toc_count": len(toc),
            "section_count": len(chunks),
            "coverage_percentage": round((len(chunks) / len(toc)) * 100, 2) if toc else 0,
        }

        with output_path.open("w", encoding="utf-8") as f:
            f.write(json.dumps(metadata, ensure_ascii=False, indent=2))

        print(f"✅ Metadata JSONL written → {output_path}")
        return output_path

    def _load_jsonl(self, path: Path):
        data = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
        return data
