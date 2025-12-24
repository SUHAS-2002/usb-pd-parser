# src/utils/validator_utils.py

class Validator:
    """
    Validation helper utilities.

    Encapsulation rules:
    - Public methods define validation intent
    - Implementation details remain private
    """

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def is_positive_int(self, value) -> bool:
        return self.__is_positive_integer(value)

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------
    def __is_positive_integer(self, value) -> bool:
        return isinstance(value, int) and value > 0
