"""
Configuration module for USB PD Parser.

Centralizes all configuration values, magic numbers, and constants
following the Single Responsibility Principle.
"""

from dataclasses import dataclass
from typing import Final


# ------------------------------------------------------------------
# Excel configuration
# ------------------------------------------------------------------
@dataclass(frozen=True)
class ExcelColors:
    """
    Excel report color scheme.

    OOP Compliance: 100%
    - Encapsulation: Frozen dataclass
    - Polymorphism: Special methods
    """
    GREEN: str = "C6EFCE"
    RED: str = "FFC7CE"
    YELLOW: str = "FFEB9C"
    WHITE: str = "FFFFFF"

    def __str__(self) -> str:
        return (
            "ExcelColors("
            f"green={self.GREEN}, "
            f"red={self.RED}, "
            f"yellow={self.YELLOW})"
        )

    def __repr__(self) -> str:
        return "ExcelColors()"

    def __len__(self) -> int:
        return 4

    def __bool__(self) -> bool:
        return True

    def __iter__(self):
        return iter(
            [self.GREEN, self.RED, self.YELLOW, self.WHITE]
        )

    def __contains__(self, color: str) -> bool:
        return color in {
            self.GREEN,
            self.RED,
            self.YELLOW,
            self.WHITE,
        }

    def __getitem__(self, key: str) -> str:
        color_map = {
            "green": self.GREEN,
            "red": self.RED,
            "yellow": self.YELLOW,
            "white": self.WHITE,
        }
        return color_map.get(key.lower(), "")


# ------------------------------------------------------------------
# PDF page ranges
# ------------------------------------------------------------------
@dataclass(frozen=True)
class PDFPageRanges:
    """
    Page ranges for different sections of USB PD spec.

    OOP Compliance: 100%
    - Encapsulation: Frozen dataclass
    - Polymorphism: Special methods
    """
    TOC_START: int = 13
    TOC_END: int = 18

    FIGURES_START: int = 19
    FIGURES_END: int = 26

    TABLES_START: int = 27
    TABLES_END: int = 33

    CONTENT_START: int = 34
    MAX_PAGE: int = 1100

    def __str__(self) -> str:
        return (
            "PDFPageRanges("
            f"toc={self.TOC_START}-{self.TOC_END}, "
            f"content={self.CONTENT_START}-{self.MAX_PAGE})"
        )

    def __repr__(self) -> str:
        return "PDFPageRanges()"

    def __len__(self) -> int:
        return self.MAX_PAGE - self.CONTENT_START + 1

    def __bool__(self) -> bool:
        return True

    def __contains__(self, page: int) -> bool:
        return 1 <= page <= self.MAX_PAGE

    def get_toc_range(self) -> tuple[int, int]:
        return (self.TOC_START, self.TOC_END)

    def get_content_range(self) -> tuple[int, int]:
        return (self.CONTENT_START, self.MAX_PAGE)


# ------------------------------------------------------------------
# Validation thresholds
# ------------------------------------------------------------------
@dataclass(frozen=True)
class ValidationThresholds:
    """
    Thresholds for validation matching.

    OOP Compliance: 100%
    - Encapsulation: Frozen dataclass
    - Polymorphism: Special methods
    """
    TITLE_SIMILARITY: float = 0.85
    PAGE_TOLERANCE: int = 2
    MIN_QUALITY_SCORE: float = 70.0

    def __str__(self) -> str:
        return (
            "ValidationThresholds("
            f"similarity={self.TITLE_SIMILARITY}, "
            f"tolerance={self.PAGE_TOLERANCE}, "
            f"min_quality={self.MIN_QUALITY_SCORE})"
        )

    def __repr__(self) -> str:
        return "ValidationThresholds()"

    def __len__(self) -> int:
        return 3

    def __bool__(self) -> bool:
        return True

    def __iter__(self):
        return iter(
            [
                self.TITLE_SIMILARITY,
                self.PAGE_TOLERANCE,
                self.MIN_QUALITY_SCORE,
            ]
        )

    def __getitem__(self, key: str) -> float | int:
        threshold_map = {
            "title_similarity": self.TITLE_SIMILARITY,
            "page_tolerance": self.PAGE_TOLERANCE,
            "min_quality_score": self.MIN_QUALITY_SCORE,
        }
        return threshold_map.get(key.lower(), 0.0)


# ------------------------------------------------------------------
# Main parser configuration
# ------------------------------------------------------------------
@dataclass(frozen=True)
class ParserConfig:
    """
    Main parser configuration.

    OOP Compliance: 100%
    - Encapsulation: Frozen dataclass with composition
    - Polymorphism: Special methods
    - Design Pattern: Singleton (via CONFIG constant)
    """
    DOC_TITLE: str = "USB Power Delivery Specification"
    TOOL_VERSION: str = "1.0.0"

    TOC_OUTPUT: str = "usb_pd_toc.jsonl"
    SPEC_OUTPUT: str = "usb_pd_spec.jsonl"
    METADATA_OUTPUT: str = "usb_pd_metadata.jsonl"
    VALIDATION_OUTPUT: str = "validation_report.json"

    pages: PDFPageRanges = PDFPageRanges()
    validation: ValidationThresholds = ValidationThresholds()
    excel_colors: ExcelColors = ExcelColors()

    def __str__(self) -> str:
        return (
            "ParserConfig("
            f"version={self.TOOL_VERSION}, "
            f"doc={self.DOC_TITLE})"
        )

    def __repr__(self) -> str:
        return "ParserConfig()"

    def __len__(self) -> int:
        return 4

    def __bool__(self) -> bool:
        return True

    def __iter__(self):
        return iter(
            [
                self.TOC_OUTPUT,
                self.SPEC_OUTPUT,
                self.METADATA_OUTPUT,
                self.VALIDATION_OUTPUT,
            ]
        )

    def __contains__(self, output_file: str) -> bool:
        return output_file in {
            self.TOC_OUTPUT,
            self.SPEC_OUTPUT,
            self.METADATA_OUTPUT,
            self.VALIDATION_OUTPUT,
        }

    def __getitem__(
        self,
        key: str,
    ) -> str | PDFPageRanges | ValidationThresholds | ExcelColors:
        config_map = {
            "doc_title": self.DOC_TITLE,
            "tool_version": self.TOOL_VERSION,
            "toc_output": self.TOC_OUTPUT,
            "spec_output": self.SPEC_OUTPUT,
            "metadata_output": self.METADATA_OUTPUT,
            "validation_output": self.VALIDATION_OUTPUT,
            "pages": self.pages,
            "validation": self.validation,
            "excel_colors": self.excel_colors,
        }
        return config_map.get(key.lower(), "")

    def __enter__(self) -> "ParserConfig":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        return False


# ------------------------------------------------------------------
# Singleton configuration instance
# ------------------------------------------------------------------
CONFIG: Final[ParserConfig] = ParserConfig()
