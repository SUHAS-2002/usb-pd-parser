# src/extractors/table_extractor.py

from typing import List, Dict, Any


class TableExtractor:
    """
    Extracts tables from PDF data.

    This implementation is a placeholder. It maintains a consistent
    interface so real table parsing can be added later without
    breaking other modules.
    """

    def extract(self, pdf_data: Any) -> List[Dict]:
        """
        Extract tables from parsed PDF data.

        Parameters
        ----------
        pdf_data : Any
            Parsed PDF content (text blocks, layout, metadata).

        Returns
        -------
        List[Dict]
            List of detected tables. Currently returns an empty list.
        """
        return []
