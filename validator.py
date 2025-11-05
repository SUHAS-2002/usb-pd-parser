#!/usr/bin/env python3
"""
USB PD Content Validator - Enhanced Version
============================================
Validates parsed content against Table of Contents with comprehensive
quality checks and detailed reporting.

Author: Enhanced Solution
Date: 2025
Version: 2.0
"""

import json
import logging
from typing import List, Dict, Set, Optional, Any
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
import re

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    """Comprehensive validation report."""
    toc_section_count: int
    parsed_section_count: int
    matched_sections: List[Dict]
    missing_sections: List[str]
    extra_sections: List[str]
    out_of_order_sections: List[Dict]
    title_mismatches: List[Dict]
    page_discrepancies: List[Dict]
    match_percentage: float
    quality_score: float
    coverage_metrics: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


class TOCValidator:
    """Enhanced validator with comprehensive quality checks."""
    
    def __init__(self, 
                 similarity_threshold: float = 0.85,
                 strict_mode: bool = False):
        """
        Initialize validator.
        
        Args:
            similarity_threshold: Minimum similarity for title matching
            strict_mode: Enable strict validation rules
        """
        self.similarity_threshold = similarity_threshold
        self.strict_mode = strict_mode
    
    def load_toc_entries(self, toc_jsonl_path: str) -> List[Dict]:
        """Load and validate ToC entries from JSONL."""
        entries = []
        seen_ids = set()
        
        logger.info(f"Loading ToC from: {toc_jsonl_path}")
        
        try:
            with open(toc_jsonl_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    
                    try:
                        entry = json.loads(line)
                        
                        # Validate required fields
                        required_fields = ['doc_title', 'section_id', 'title', 
                                         'full_path', 'page', 'level']
                        missing = [f for f in required_fields if f not in entry]
                        
                        if missing:
                            logger.warning(
                                f"Line {line_num}: Missing fields {missing}"
                            )
                            continue
                        
                        # Check for duplicates
                        section_id = entry['section_id']
                        if section_id in seen_ids:
                            logger.warning(
                                f"Line {line_num}: Duplicate section {section_id}"
                            )
                            continue
                        
                        seen_ids.add(section_id)
                        entries.append(entry)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Line {line_num}: Invalid JSON - {e}")
                        continue
                        
        except FileNotFoundError:
            logger.error(f"ToC file not found: {toc_jsonl_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading ToC: {e}")
            raise
        
        logger.info(f"Loaded {len(entries)} valid ToC entries")
        return entries
    
    def load_chunks(self, chunks_jsonl_path: str) -> List[Dict]:
        """Load and validate content chunks from JSONL."""
        chunks = []
        seen_ids = set()
        
        logger.info(f"Loading content chunks from: {chunks_jsonl_path}")
        
        try:
            with open(chunks_jsonl_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    
                    try:
                        chunk = json.loads(line)
                        
                        # Validate required fields
                        required_fields = ['doc_title', 'section_id', 
                                         'section_path', 'start_heading',
                                         'start_page', 'end_page', 'content']
                        missing = [f for f in required_fields if f not in chunk]
                        
                        if missing:
                            logger.warning(
                                f"Line {line_num}: Missing fields {missing}"
                            )
                            continue
                        
                        # Check for duplicates
                        section_id = chunk['section_id']
                        if section_id in seen_ids:
                            logger.warning(
                                f"Line {line_num}: Duplicate section {section_id}"
                            )
                            continue
                        
                        seen_ids.add(section_id)
                        chunks.append(chunk)
                        
                    except json.JSONDecodeError as e:
                        logger.error(f"Line {line_num}: Invalid JSON - {e}")
                        continue
                        
        except FileNotFoundError:
            logger.error(f"Content file not found: {chunks_jsonl_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading chunks: {e}")
            raise
        
        logger.info(f"Loaded {len(chunks)} valid content chunks")
        return chunks
    
    def fuzzy_match(self, str1: str, str2: str) -> float:
        """
        Calculate fuzzy string similarity with normalization.
        
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Normalize strings
        s1 = self._normalize_string(str1)
        s2 = self._normalize_string(str2)
        
        return SequenceMatcher(None, s1, s2).ratio()
    
    def _normalize_string(self, s: str) -> str:
        """Normalize string for comparison."""
        # Convert to lowercase
        s = s.lower()
        # Remove extra whitespace
        s = re.sub(r'\s+', ' ', s)
        # Remove punctuation
        s = re.sub(r'[^\w\s]', '', s)
        return s.strip()
    
    def match_sections(self, 
                      toc_entries: List[Dict], 
                      chunks: List[Dict]) -> Dict[str, List]:
        """
        Match ToC entries to content chunks with detailed analysis.
        
        Returns:
            Dictionary with matched, missing, extra, and mismatched sections
        """
        logger.info("Matching sections between ToC and content...")
        
        toc_map = {e['section_id']: e for e in toc_entries}
        chunk_map = {c['section_id']: c for c in chunks}
        
        matched = []
        missing = []
        extra = []
        title_mismatches = []
        
        # Find matches and analyze title similarity
        for section_id, toc_entry in toc_map.items():
            if section_id in chunk_map:
                chunk = chunk_map[section_id]
                similarity = self.fuzzy_match(
                    toc_entry['title'], 
                    chunk['start_heading']
                )
                
                match_info = {
                    'section_id': section_id,
                    'toc_title': toc_entry['title'],
                    'chunk_title': chunk['start_heading'],
                    'similarity': similarity,
                    'page_match': toc_entry['page'] == chunk['start_page']
                }
                
                matched.append(match_info)
                
                # Flag title mismatches
                if similarity < self.similarity_threshold:
                    title_mismatches.append({
                        'section_id': section_id,
                        'toc_title': toc_entry['title'],
                        'content_title': chunk['start_heading'],
                        'similarity': similarity
                    })
            else:
                missing.append({
                    'section_id': section_id,
                    'full_path': toc_entry['full_path'],
                    'page': toc_entry['page']
                })
        
        # Find extra sections in content
        for section_id, chunk in chunk_map.items():
            if section_id not in toc_map:
                extra.append({
                    'section_id': section_id,
                    'section_path': chunk['section_path'],
                    'page': chunk['start_page']
                })
        
        logger.info(f"Matched: {len(matched)}, Missing: {len(missing)}, "
                   f"Extra: {len(extra)}")
        
        return {
            'matched': matched,
            'missing': missing,
            'extra': extra,
            'title_mismatches': title_mismatches
        }
    
    def check_order(self, 
                   toc_entries: List[Dict], 
                   chunks: List[Dict]) -> List[Dict]:
        """
        Verify sections are in correct hierarchical order.
        
        Returns:
            List of out-of-order sections with details
        """
        logger.info("Checking section order...")
        
        toc_order = {e['section_id']: i for i, e in enumerate(toc_entries)}
        out_of_order = []
        
        prev_toc_index = -1
        for i, chunk in enumerate(chunks):
            section_id = chunk['section_id']
            
            if section_id in toc_order:
                current_toc_index = toc_order[section_id]
                
                if current_toc_index < prev_toc_index:
                    out_of_order.append({
                        'section_id': section_id,
                        'section_path': chunk['section_path'],
                        'expected_position': current_toc_index,
                        'actual_position': i,
                        'severity': 'high' if current_toc_index < prev_toc_index - 5 
                                   else 'low'
                    })
                
                prev_toc_index = current_toc_index
        
        if out_of_order:
            logger.warning(f"Found {len(out_of_order)} out-of-order sections")
        else:
            logger.info("All sections in correct order")
        
        return out_of_order
    
    def check_page_consistency(self, 
                              toc_entries: List[Dict], 
                              chunks: List[Dict]) -> List[Dict]:
        """Check for page number discrepancies."""
        logger.info("Checking page consistency...")
        
        discrepancies = []
        chunk_map = {c['section_id']: c for c in chunks}
        
        for toc_entry in toc_entries:
            section_id = toc_entry['section_id']
            
            if section_id in chunk_map:
                chunk = chunk_map[section_id]
                toc_page = toc_entry['page']
                chunk_page = chunk['start_page']
                
                # Allow small variance (PDF extraction may differ)
                if abs(toc_page - chunk_page) > 2:
                    discrepancies.append({
                        'section_id': section_id,
                        'title': toc_entry['title'],
                        'toc_page': toc_page,
                        'content_page': chunk_page,
                        'difference': abs(toc_page - chunk_page)
                    })
        
        if discrepancies:
            logger.warning(f"Found {len(discrepancies)} page discrepancies")
        
        return discrepancies
    
    def calculate_coverage(self, 
                          toc_entries: List[Dict], 
                          chunks: List[Dict]) -> Dict[str, Any]:
        """Calculate detailed coverage metrics."""
        coverage = {
            'total_sections': len(toc_entries),
            'extracted_sections': len(chunks),
            'by_level': {},
            'completeness_by_level': {}
        }
        
        # Count by level
        toc_by_level = {}
        chunks_by_level = {}
        
        for entry in toc_entries:
            level = entry['level']
            toc_by_level[level] = toc_by_level.get(level, 0) + 1
        
        chunk_ids = {c['section_id'] for c in chunks}
        for entry in toc_entries:
            if entry['section_id'] in chunk_ids:
                level = entry['level']
                chunks_by_level[level] = chunks_by_level.get(level, 0) + 1
        
        # Calculate percentages
        for level in toc_by_level:
            extracted = chunks_by_level.get(level, 0)
            total = toc_by_level[level]
            coverage['by_level'][level] = {
                'total': total,
                'extracted': extracted,
                'percentage': (extracted / total * 100) if total > 0 else 0
            }
        
        return coverage
    
    def calculate_quality_score(self, 
                               match_percentage: float,
                               title_mismatches: int,
                               out_of_order: int,
                               page_discrepancies: int,
                               total_sections: int) -> float:
        """
        Calculate overall quality score (0-100).
        
        Factors:
        - Match percentage: 60% weight
        - Title accuracy: 20% weight
        - Order correctness: 10% weight
        - Page accuracy: 10% weight
        """
        if total_sections == 0:
            return 0.0
        
        # Match percentage component (60%)
        match_score = match_percentage * 0.6
        
        # Title accuracy component (20%)
        title_accuracy = max(0, 100 - (title_mismatches / total_sections * 100))
        title_score = title_accuracy * 0.2
        
        # Order correctness component (10%)
        order_accuracy = max(0, 100 - (out_of_order / total_sections * 100))
        order_score = order_accuracy * 0.1
        
        # Page accuracy component (10%)
        page_accuracy = max(0, 100 - (page_discrepancies / total_sections * 100))
        page_score = page_accuracy * 0.1
        
        quality_score = match_score + title_score + order_score + page_score
        
        return round(quality_score, 2)
    
    def validate(self, 
                toc_jsonl_path: str, 
                chunks_jsonl_path: str) -> ValidationReport:
        """
        Run comprehensive validation pipeline.
        
        Returns:
            ValidationReport with all metrics and analysis
        """
        logger.info("=" * 70)
        logger.info("Starting Comprehensive Validation")
        logger.info("=" * 70)
        
        # Load data
        toc_entries = self.load_toc_entries(toc_jsonl_path)
        chunks = self.load_chunks(chunks_jsonl_path)
        
        if not toc_entries:
            logger.error("No ToC entries loaded - cannot validate")
            raise ValueError("Empty ToC file")
        
        # Match sections
        match_results = self.match_sections(toc_entries, chunks)
        
        # Check order
        out_of_order = self.check_order(toc_entries, chunks)
        
        # Check page consistency
        page_discrepancies = self.check_page_consistency(toc_entries, chunks)
        
        # Calculate coverage
        coverage_metrics = self.calculate_coverage(toc_entries, chunks)
        
        # Calculate match percentage
        match_pct = (len(match_results['matched']) / len(toc_entries) * 100) \
                    if toc_entries else 0
        
        # Calculate quality score
        quality_score = self.calculate_quality_score(
            match_pct,
            len(match_results['title_mismatches']),
            len(out_of_order),
            len(page_discrepancies),
            len(toc_entries)
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            match_pct, match_results, out_of_order, 
            page_discrepancies, coverage_metrics
        )
        
        # Create report
        report = ValidationReport(
            toc_section_count=len(toc_entries),
            parsed_section_count=len(chunks),
            matched_sections=match_results['matched'],
            missing_sections=match_results['missing'],
            extra_sections=match_results['extra'],
            out_of_order_sections=out_of_order,
            title_mismatches=match_results['title_mismatches'],
            page_discrepancies=page_discrepancies,
            match_percentage=match_pct,
            quality_score=quality_score,
            coverage_metrics=coverage_metrics,
            recommendations=recommendations
        )
        
        logger.info(f"Validation complete: {match_pct:.1f}% match, "
                   f"{quality_score:.1f} quality score")
        
        return report
    
    def _generate_recommendations(self,
                                 match_pct: float,
                                 match_results: Dict,
                                 out_of_order: List,
                                 page_discrepancies: List,
                                 coverage: Dict) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []
        
        if match_pct < 95:
            recommendations.append(
                f"Coverage is {match_pct:.1f}% - review missing sections "
                "and adjust extraction logic"
            )
        
        if len(match_results['title_mismatches']) > 0:
            recommendations.append(
                f"Found {len(match_results['title_mismatches'])} title "
                "mismatches - verify heading extraction patterns"
            )
        
        if len(out_of_order) > 0:
            recommendations.append(
                f"Found {len(out_of_order)} out-of-order sections - "
                "check PDF structure and parsing logic"
            )
        
        if len(page_discrepancies) > 5:
            recommendations.append(
                f"Found {len(page_discrepancies)} page discrepancies - "
                "verify page numbering consistency"
            )
        
        # Check level-specific coverage
        for level, metrics in coverage['by_level'].items():
            if metrics['percentage'] < 80:
                recommendations.append(
                    f"Level {level} coverage is only {metrics['percentage']:.1f}% "
                    f"({metrics['extracted']}/{metrics['total']}) - "
                    "improve extraction for this hierarchy level"
                )
        
        if not recommendations:
            recommendations.append("Excellent! All validation checks passed.")
        
        return recommendations
    
    def generate_report(self, 
                       report: ValidationReport, 
                       output_path: str = "validation_report.json") -> Dict:
        """
        Generate and save detailed validation report.
        
        Returns:
            Report dictionary
        """
        logger.info(f"Generating report: {output_path}")
        
        report_dict = {
            'summary': {
                'toc_sections': report.toc_section_count,
                'parsed_sections': report.parsed_section_count,
                'matched_sections': len(report.matched_sections),
                'match_percentage': report.match_percentage,
                'quality_score': report.quality_score,
                'status': self._get_status(report.quality_score)
            },
            'coverage_metrics': report.coverage_metrics,
            'issues': {
                'missing_sections': {
                    'count': len(report.missing_sections),
                    'details': report.missing_sections[:10]  # Limit output
                },
                'extra_sections': {
                    'count': len(report.extra_sections),
                    'details': report.extra_sections[:10]
                },
                'title_mismatches': {
                    'count': len(report.title_mismatches),
                    'details': report.title_mismatches[:10]
                },
                'out_of_order_sections': {
                    'count': len(report.out_of_order_sections),
                    'details': report.out_of_order_sections[:10]
                },
                'page_discrepancies': {
                    'count': len(report.page_discrepancies),
                    'details': report.page_discrepancies[:10]
                }
            },
            'recommendations': report.recommendations,
            'validation_timestamp': self._get_timestamp()
        }
        
        # Save to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Report saved to: {output_path}")
        
        # Print summary to console
        self._print_summary(report)
        
        return report_dict
    
    def _get_status(self, quality_score: float) -> str:
        """Get status based on quality score."""
        if quality_score >= 95:
            return "EXCELLENT"
        elif quality_score >= 85:
            return "GOOD"
        elif quality_score >= 70:
            return "ACCEPTABLE"
        else:
            return "NEEDS IMPROVEMENT"
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _print_summary(self, report: ValidationReport) -> None:
        """Print validation summary to console."""
        print("\n" + "=" * 70)
        print("VALIDATION REPORT SUMMARY")
        print("=" * 70)
        print(f"Status: {self._get_status(report.quality_score)}")
        print(f"Quality Score: {report.quality_score:.1f}/100")
        print(f"\nSection Coverage:")
        print(f"  ToC Sections: {report.toc_section_count}")
        print(f"  Parsed Sections: {report.parsed_section_count}")
        print(f"  Matched: {len(report.matched_sections)} "
              f"({report.match_percentage:.1f}%)")
        print(f"\nIssues Detected:")
        print(f"  Missing Sections: {len(report.missing_sections)}")
        print(f"  Extra Sections: {len(report.extra_sections)}")
        print(f"  Title Mismatches: {len(report.title_mismatches)}")
        print(f"  Out of Order: {len(report.out_of_order_sections)}")
        print(f"  Page Discrepancies: {len(report.page_discrepancies)}")
        
        if report.coverage_metrics.get('by_level'):
            print(f"\nCoverage by Level:")
            for level, metrics in sorted(report.coverage_metrics['by_level'].items()):
                print(f"  Level {level}: {metrics['extracted']}/{metrics['total']} "
                      f"({metrics['percentage']:.1f}%)")
        
        if report.recommendations:
            print(f"\nRecommendations:")
            for i, rec in enumerate(report.recommendations, 1):
                print(f"  {i}. {rec}")
        
        print("=" * 70 + "\n")


def main():
    """Run validation from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='USB PD Content Validator v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument('toc_file', help='Path to ToC JSONL file')
    parser.add_argument('chunks_file', help='Path to content chunks JSONL file')
    parser.add_argument('-o', '--output', default='validation_report.json',
                       help='Output report path (default: validation_report.json)')
    parser.add_argument('-t', '--threshold', type=float, default=0.85,
                       help='Similarity threshold for title matching (default: 0.85)')
    parser.add_argument('--strict', action='store_true',
                       help='Enable strict validation mode')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    try:
        validator = TOCValidator(
            similarity_threshold=args.threshold,
            strict_mode=args.strict
        )
        
        report = validator.validate(args.toc_file, args.chunks_file)
        validator.generate_report(report, args.output)
        
        # Exit with appropriate code
        if report.quality_score >= 85:
            return 0
        elif report.quality_score >= 70:
            return 1
        else:
            return 2
            
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=args.verbose)
        return 3


if __name__ == '__main__':
    exit(main())