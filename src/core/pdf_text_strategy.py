from abc import ABC, abstractmethod
from typing import Any

class PDFTextStrategy(ABC):
    @abstractmethod
    def extract_text(self, pdf_path: str) -> Any:
        pass
