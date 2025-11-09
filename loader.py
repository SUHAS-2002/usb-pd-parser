import json
import logging
from typing import List, Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class DataLoader:
    """Handles loading and basic validation of JSONL files."""

    def _load_jsonl(self, path: str, required: List[str]) -> List[Dict]:
        file_path = Path(path)
        if not file_path.exists():
            logger.error(f"File not found: {path}")
            raise FileNotFoundError(path)

        entries = []
        seen = set()

        with file_path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    missing = [f for f in required if f not in data]
                    if missing:
                        logger.warning(f"Line {i}: missing {missing}")
                        continue
                    sid = data["section_id"]
                    if sid in seen:
                        logger.warning(f"Line {i}: duplicate {sid}")
                        continue
                    seen.add(sid)
                    entries.append(data)
                except json.JSONDecodeError as e:
                    logger.error(f"Line {i}: JSON error - {e}")

        logger.info(f"Loaded {len(entries)} entries from {path}")
        return entries

    def load_toc(self, path: str) -> List[Dict]:
        required = ["section_id", "title", "page", "level", "full_path"]
        return self._load_jsonl(path, required)

    def load_chunks(self, path: str) -> List[Dict]:
        required = ["section_id", "start_heading", "start_page", "content"]
        return self._load_jsonl(path, required)