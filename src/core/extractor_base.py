# src/core/extractor_base.py

from abc import ABC, abstractmethod
from typing import List, Dict


class BaseExtractor(ABC):
    """
    Abstract base class for all PDF extraction strategies.

    All extractors must implement the extract() method and return a list of
    dictionaries, one per page or extracted unit.
    """

    @abstractmethod
    def extract(self, pdf_path: str) -> List[Dict]:
        """
        Extract data from a PDF file.

        Parameters
        ----------
        pdf_path : str
            Path to the PDF file.

        Returns
        -------
        List[Dict]
            A list where each entry contains extracted data.
        """
        raise NotImplementedError
