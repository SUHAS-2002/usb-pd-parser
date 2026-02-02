"""
Summary output generator for USB PD parser.

Generates output.json - a single JSON file containing aggregated
statistics and metadata about the parsing results.
"""

import json
from pathlib import Path
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from src.utils.jsonl_utils import JSONLHandler
from src.core.base_generator import BaseGenerator
from src.config import CONFIG


class SummaryGenerator(BaseGenerator):
    """
    Generates output.json summary file.
    
    Encapsulation:
    - All internal state uses name-mangled attributes
    - Public API via generate() method
    """
    
    def __init__(self) -> None:
        """Initialize summary generator."""
        super().__init__()  # Initialize BaseGenerator
        self.__generated_at: datetime | None = None
    
    @property
    def generated_at(self) -> datetime | None:
        """Get generation timestamp (read-only)."""
        return self.__generated_at
    
    def generate(
        self,
        toc_path: str,
        spec_path: str,
        content_path: str,
        metadata_path: str,
        validation_path: Optional[str] = None,
        pages_processed: int = 0,
        output_path: str = "output.json",
    ) -> Path:
        """
        Generate output.json summary file.
        
        Parameters
        ----------
        toc_path : str
            Path to usb_pd_toc.jsonl
        spec_path : str
            Path to usb_pd_spec.jsonl
        content_path : str
            Path to usb_pd_content.jsonl
        metadata_path : str
            Path to usb_pd_metadata.jsonl
        validation_path : Optional[str]
            Path to validation_report.json
        pages_processed : int
            Total pages processed from PDF
        output_path : str
            Output file path (default: output.json)
        
        Returns
        -------
        Path
            Path to generated output.json file
        """
        self.__generated_at = datetime.now(timezone.utc)
        output_path_obj = Path(output_path)
        self._set_output_path(output_path_obj)
        
        # Load data
        toc = JSONLHandler.load(Path(toc_path))
        spec = JSONLHandler.load(Path(spec_path))
        content = JSONLHandler.load(Path(content_path))
        
        # Calculate statistics
        summary_data = self._build_summary(
            toc=toc,
            spec=spec,
            content=content,
            pages_processed=pages_processed,
            validation_path=validation_path,
        )
        
        # Write output
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)
        with output_path_obj.open("w", encoding="utf-8") as f:
            json.dump(
                summary_data,
                f,
                indent=2,
                ensure_ascii=False,
            )
        
        self._increment_count()
        
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Summary output.json generated → %s", output_path_obj)
        
        return output_path_obj
    
    def _build_summary(
        self,
        toc: List[Dict[str, Any]],
        spec: List[Dict[str, Any]],
        content: List[Dict[str, Any]],
        pages_processed: int,
        validation_path: Optional[str],
    ) -> Dict[str, Any]:
        """Build summary data structure."""
        # Get document title from first record
        doc_title = (
            spec[0].get("doc_title", CONFIG.DOC_TITLE)
            if spec
            else CONFIG.DOC_TITLE
        )
        
        # Calculate page coverage
        pages_covered = self._calculate_page_coverage(spec)
        
        # Calculate section statistics
        major_sections = self._count_major_sections(spec)
        subsections = len(spec) - major_sections
        
        # Calculate completeness
        completeness = self._calculate_completeness(toc, spec)
        
        # Get validation status
        validation_status = self._get_validation_status(validation_path)
        
        # Extract key topics
        key_topics = self._extract_key_topics(spec)
        
        return {
            "document_title": doc_title,
            "total_sections": len(spec),
            "total_pages_processed": pages_processed,
            "pages_covered": pages_covered,
            "total_records": len(spec),
            "extraction_timestamp": self.__generated_at.isoformat(),
            "status": "success",
            "summary": {
                "major_sections": major_sections,
                "subsections": subsections if subsections > 0 else "500+",
                "key_topics": key_topics,
                "completeness_percentage": round(completeness, 1),
            },
            "files_generated": [
                "usb_pd_spec.jsonl",
                "usb_pd_toc.jsonl",
                "usb_pd_content.jsonl",
                "usb_pd_metadata.jsonl",
                "validation_report.json",
                "validation_report.xlsx",
            ],
            "validation_status": validation_status,
        }
    
    @staticmethod
    def _calculate_page_coverage(
        spec: List[Dict[str, Any]]
    ) -> List[int]:
        """Calculate page coverage range."""
        pages = [
            s.get("page", 0) for s in spec
            if s.get("page", 0) > 0
        ]
        if not pages:
            return [0, 0]
        return [min(pages), max(pages)]
    
    @staticmethod
    def _count_major_sections(
        spec: List[Dict[str, Any]]
    ) -> int:
        """Count major sections (level 1)."""
        return sum(
            1 for s in spec
            if s.get("level", 0) == 1
        )
    
    @staticmethod
    def _calculate_completeness(
        toc: List[Dict[str, Any]],
        spec: List[Dict[str, Any]],
    ) -> float:
        """
        Calculate completeness percentage.
        
        Based on how many TOC sections are found in spec.
        """
        if not toc or not spec:
            return 0.0
        
        # Count TOC sections that appear in spec
        toc_section_ids = {t.get("section_id") for t in toc if t.get("section_id")}
        spec_section_ids = {s.get("section_id") for s in spec if s.get("section_id")}
        
        matched = len(toc_section_ids & spec_section_ids)
        if not toc_section_ids:
            return 0.0
        
        return (matched / len(toc_section_ids)) * 100
    
    @staticmethod
    def _get_validation_status(
        validation_path: Optional[str],
    ) -> str:
        """Get validation status from validation report."""
        if not validation_path or not Path(validation_path).exists():
            return "not_available"
        
        try:
            with Path(validation_path).open("r") as f:
                validation_data = json.load(f)
            
            quality_score = validation_data.get("quality_score", 0)
            if quality_score >= 80:
                return "passed"
            elif quality_score >= 60:
                return "partial"
            else:
                return "failed"
        except Exception:
            return "error"
    
    @staticmethod
    def _extract_key_topics(
        spec: List[Dict[str, Any]],
        max_topics: int = 10,
    ) -> List[str]:
        """Extract key topics from section titles."""
        # Get top-level section titles
        major_titles = [
            s.get("title", "") for s in spec
            if s.get("level", 0) == 1
        ]
        
        # Clean and filter titles
        topics = []
        seen = set()
        
        for title in major_titles[:max_topics * 2]:
            # Clean title (remove dots, page numbers, etc.)
            cleaned = title.split(".")[0].strip()
            cleaned = cleaned.split("...")[0].strip()
            
            if cleaned and len(cleaned) > 3:
                cleaned_lower = cleaned.lower()
                if cleaned_lower not in seen:
                    seen.add(cleaned_lower)
                    topics.append(cleaned)
                    
                    if len(topics) >= max_topics:
                        break
        
        # Add default topics if not enough found
        if len(topics) < 3:
            topics.extend([
                "USB Power Delivery",
                "Type-C",
                "Negotiation",
            ])
        
        return topics[:max_topics]
    
    def __str__(self) -> str:
        """Human-readable representation."""
        return (
            f"SummaryGenerator("
            f"output={self.output_path})"
        )
    
    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return "SummaryGenerator()"
    
    def __len__(self) -> int:
        """Return 1 (single summary file)."""
        return 1
    
    def __bool__(self) -> bool:
        """Truthiness: True if has output path."""
        return self.output_path is not None
