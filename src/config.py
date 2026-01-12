# src/config.py

"""
Configuration module for USB PD Parser.

Centralizes all configuration values, magic numbers, and constants
following the Single Responsibility Principle.
"""

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class ExcelColors:
    """Excel report color scheme."""
    GREEN: str = "C6EFCE"
    RED: str = "FFC7CE"
    YELLOW: str = "FFEB9C"
    WHITE: str = "FFFFFF"


@dataclass(frozen=True)
class PDFPageRanges:
    """Page ranges for different sections of USB PD spec."""
    TOC_START: int = 13
    TOC_END: int = 18

    FIGURES_START: int = 19
    FIGURES_END: int = 26

    TABLES_START: int = 27
    TABLES_END: int = 33

    CONTENT_START: int = 34
    MAX_PAGE: int = 1100


@dataclass(frozen=True)
class ValidationThresholds:
    """Thresholds for validation matching."""
    TITLE_SIMILARITY: float = 0.85
    PAGE_TOLERANCE: int = 2
    MIN_QUALITY_SCORE: float = 70.0


@dataclass(frozen=True)
class ParserConfig:
    """Main parser configuration."""
    DOC_TITLE: str = "USB Power Delivery Specification"
    TOOL_VERSION: str = "1.0.0"

    TOC_OUTPUT: str = "usb_pd_toc.jsonl"
    SPEC_OUTPUT: str = "usb_pd_spec.jsonl"
    METADATA_OUTPUT: str = "usb_pd_metadata.jsonl"
    VALIDATION_OUTPUT: str = "validation_report.json"

    pages: PDFPageRanges = PDFPageRanges()
    validation: ValidationThresholds = ValidationThresholds()
    excel_colors: ExcelColors = ExcelColors()


CONFIG: Final[ParserConfig] = ParserConfig()
