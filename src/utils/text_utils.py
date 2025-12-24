# src/utils/text_utils.py

from typing import Optional


class TextUtils:
    """
    Text cleaning utilities.

    Encapsulation rules:
    - Public methods provide stable API
    - Internal normalization logic is private
    """

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def normalize_whitespace(self, text: Optional[str]) -> str:
        if text is None:
            return ""
        return self.__collapse_whitespace(text)

    # ---------------------------------------------------------
    def safe_strip(self, text: Optional[str]) -> str:
        if text is None:
            return ""
        return self.__strip(text)

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------
    def __collapse_whitespace(self, text: str) -> str:
        return " ".join(text.split())

    # ---------------------------------------------------------
    def __strip(self, text: str) -> str:
        return text.strip()
