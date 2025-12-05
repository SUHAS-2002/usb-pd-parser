# src/extractors/table_extractor.py
from typing import List, Dict, Any


class TableExtractor:
    """
    Extracts tables from PDF data.

    Currently implemented as a placeholder (no real table detection),
    but structured for future extension.

    Responsibilities:
    - Provide a consistent interface for table extraction.
    - Allow easy upgrade to real table parsing without breaking other modules.
    """

    def extract(self, pdf_data: Any) -> List[Dict]:
        """
        Extract tables from parsed PDF data.

        Parameters
        ----------
        pdf_data : Any
            The parsed PDF content (text blocks, layout info, etc.)

        Returns
        -------
        List[Dict]
            A list of table representations. Currently empty.
        """
        # Placeholder: No tables detected
        return []