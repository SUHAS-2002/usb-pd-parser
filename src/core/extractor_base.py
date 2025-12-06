from abc import ABC, abstractmethod
from typing import List, Dict

class BaseExtractor(ABC):
    """
    Abstract base class for all PDF extraction strategies.
    All extractors MUST implement extract().
    """

    @abstractmethod
    def extract(self, pdf_path: str) -> List[Dict]:
        """Return list of extracted page dicts."""
        pass
