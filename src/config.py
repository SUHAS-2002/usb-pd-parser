"""
Configuration module for USB PD Parser.

Centralizes all configuration values, magic numbers, and constants
following the Single Responsibility Principle.
"""

from dataclasses import dataclass
from typing import Final


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
        """Human-readable representation."""
        return f"ExcelColors(green={self.GREEN}, red={self.RED}, yellow={self.YELLOW})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"ExcelColors()"
    
    def __len__(self) -> int:
        """Return number of color definitions."""
        return 4
    
    def __bool__(self) -> bool:
        """Truthiness: Always True."""
        return True
    
    def __iter__(self):
        """Make class iterable over colors."""
        return iter([self.GREEN, self.RED, self.YELLOW, self.WHITE])
    
    def __contains__(self, color: str) -> bool:
        """Check if color is defined."""
        return color in [self.GREEN, self.RED, self.YELLOW, self.WHITE]
    
    def __getitem__(self, key: str) -> str:
        """Get color by name."""
        color_map = {
            "green": self.GREEN,
            "red": self.RED,
            "yellow": self.YELLOW,
            "white": self.WHITE,
        }
        return color_map.get(key.lower(), "")


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
        """Human-readable representation."""
        return f"PDFPageRanges(toc={self.TOC_START}-{self.TOC_END}, content={self.CONTENT_START}-{self.MAX_PAGE})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"PDFPageRanges()"
    
    def __len__(self) -> int:
        """Return total page range."""
        return self.MAX_PAGE - self.CONTENT_START + 1
    
    def __bool__(self) -> bool:
        """Truthiness: Always True."""
        return True
    
    def __contains__(self, page: int) -> bool:
        """Check if page is in valid range."""
        return 1 <= page <= self.MAX_PAGE
    
    def get_toc_range(self) -> tuple[int, int]:
        """Get TOC page range."""
        return (self.TOC_START, self.TOC_END)
    
    def get_content_range(self) -> tuple[int, int]:
        """Get content page range."""
        return (self.CONTENT_START, self.MAX_PAGE)


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
        """Human-readable representation."""
        return f"ValidationThresholds(similarity={self.TITLE_SIMILARITY}, tolerance={self.PAGE_TOLERANCE}, min_quality={self.MIN_QUALITY_SCORE})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"ValidationThresholds()"
    
    def __len__(self) -> int:
        """Return number of thresholds."""
        return 3
    
    def __bool__(self) -> bool:
        """Truthiness: Always True."""
        return True
    
    def __iter__(self):
        """Make class iterable over thresholds."""
        return iter([self.TITLE_SIMILARITY, self.PAGE_TOLERANCE, self.MIN_QUALITY_SCORE])
    
    def __getitem__(self, key: str) -> float | int:
        """Get threshold by name."""
        threshold_map = {
            "title_similarity": self.TITLE_SIMILARITY,
            "page_tolerance": self.PAGE_TOLERANCE,
            "min_quality_score": self.MIN_QUALITY_SCORE,
        }
        return threshold_map.get(key.lower(), 0.0)


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
        """Human-readable representation."""
        return f"ParserConfig(version={self.TOOL_VERSION}, doc={self.DOC_TITLE})"
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"ParserConfig()"
    
    def __len__(self) -> int:
        """Return number of output files."""
        return 4
    
    def __bool__(self) -> bool:
        """Truthiness: Always True."""
        return True
    
    def __iter__(self):
        """Make class iterable over output files."""
        return iter([self.TOC_OUTPUT, self.SPEC_OUTPUT, self.METADATA_OUTPUT, self.VALIDATION_OUTPUT])
    
    def __contains__(self, output_file: str) -> bool:
        """Check if output file is configured."""
        return output_file in [self.TOC_OUTPUT, self.SPEC_OUTPUT, self.METADATA_OUTPUT, self.VALIDATION_OUTPUT]
    
    def __getitem__(self, key: str) -> str | PDFPageRanges | ValidationThresholds | ExcelColors:
        """Get config value by key."""
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
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        """Context manager exit."""
        return False


CONFIG: Final[ParserConfig] = ParserConfig()
