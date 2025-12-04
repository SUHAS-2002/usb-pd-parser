class TextUtils:
    """Text cleaning helpers."""

    @staticmethod
    def normalize_whitespace(text: str) -> str:
        if text is None:
            return ""
        return " ".join(text.split())

    @staticmethod
    def safe_strip(text: str) -> str:
        if text is None:
            return ""
        return text.strip()
