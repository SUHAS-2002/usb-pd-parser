class Validator:
    """Small utilities for validation."""

    @staticmethod
    def is_positive_int(value) -> bool:
        return isinstance(value, int) and value > 0
