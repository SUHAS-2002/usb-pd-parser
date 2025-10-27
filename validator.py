import json
import logging
from typing import List, Dict, Set
from dataclasses import dataclass
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)


@dataclass
class ValidationReport:
    """Report of validation results."""
    toc_section_count: int
    parsed_section_count: int
    missing_sections: List[str]
    extra_sections: List[str]
    out_of_order_sections: List[Dict]
    matched_sections: List[Dict]
    match_percentage: float


class TOCValidator:
    """Validates parsed content against Table of Contents."""
    
    def __init__(self, similarity_threshold: float = 0.85):
        self.similarity_threshold = similarity_threshold
    
    def load_toc_entries(self, toc_jsonl_path: str) -> List[Dict]:
        """Load ToC entries from JSONL file."""
        entries = []
        with open(toc_jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        logger.info(f"Loaded {len(entries)} ToC entries")
        return entries
    
    def load_chunks(self, chunks_jsonl_path: str) -> List[Dict]:
        """Load content chunks from JSONL file."""
        chunks = []
        with open(chunks_jsonl_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    chunks.append(json.loads(line))
        logger.info(f"Loaded {len(chunks)} content chunks")
        return chunks
    
    def fuzzy_match(self, str1: str, str2: str) -> float:
        """Calculate fuzzy string similarity."""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    def match_sections(self, toc_entries: List[Dict], chunks: List[Dict]) -> Dict:
        """Match ToC entries to content chunks."""
        toc_ids = {entry['section_id']: entry for entry in toc_entries}
        chunk_ids = {chunk['section_id']: chunk for chunk in chunks}
        
        matched = []
        missing = []
        extra = []
        
        # Find matches and missing sections
        for section_id, toc_entry in toc_ids.items():
            if section_id in chunk_ids:
                chunk = chunk_ids[section_id]
                similarity = self.fuzzy_match(toc_entry['title'], chunk['start_heading'])
                matched.append({
                    'section_id': section_id,
                    'toc_title': toc_entry['title'],
                    'chunk_title': chunk['start_heading'],
                    'similarity': similarity
                })
            else:
                missing.append(toc_entry['full_path'])
        
        # Find extra sections
        for section_id in chunk_ids:
            if section_id not in toc_ids:
                extra.append(chunk_ids[section_id]['section_path'])
        
        return {
            'matched': matched,
            'missing': missing,
            'extra': extra
        }
    
    def check_order(self, toc_entries: List[Dict], chunks: List[Dict]) -> List[Dict]:
        """Check if sections are in correct order."""
        out_of_order = []
        
        toc_order = {entry['section_id']: i for i, entry in enumerate(toc_entries)}
        
        prev_index = -1
        for i, chunk in enumerate(chunks):
            section_id = chunk['section_id']
            if section_id in toc_order:
                current_index = toc_order[section_id]
                if current_index < prev_index:
                    out_of_order.append({
                        'section_id': section_id,
                        'expected_position': current_index,
                        'actual_position': i
                    })
                prev_index = current_index
        
        return out_of_order
    
    def validate(self, toc_jsonl_path: str, chunks_jsonl_path: str) -> ValidationReport:
        """Run complete validation."""
        logger.info("Starting validation...")
        
        # Load data
        toc_entries = self.load_toc_entries(toc_jsonl_path)
        chunks = self.load_chunks(chunks_jsonl_path)
        
        # Match sections
        match_results = self.match_sections(toc_entries, chunks)
        
        # Check order
        out_of_order = self.check_order(toc_entries, chunks)
        
        # Calculate match percentage
        match_percentage = (len(match_results['matched']) / len(toc_entries) * 100) if toc_entries else 0
        
        # Create report
        report = ValidationReport(
            toc_section_count=len(toc_entries),
            parsed_section_count=len(chunks),
            missing_sections=match_results['missing'],
            extra_sections=match_results['extra'],
            out_of_order_sections=out_of_order,
            matched_sections=match_results['matched'],
            match_percentage=match_percentage
        )
        
        logger.info(f"Validation complete: {match_percentage:.1f}% match")
        return report
    
    def generate_report(self, report: ValidationReport, output_path: str = "validation_report.json"):
        """Generate and save validation report."""
        report_dict = {
            'summary': f"Parsed {report.parsed_section_count} of {report.toc_section_count} ToC sections ({report.match_percentage:.1f}% match)",
            'metrics': {
                'toc_sections': report.toc_section_count,
                'parsed_sections': report.parsed_section_count,
                'matched_sections': len(report.matched_sections),
                'missing_sections': len(report.missing_sections),
                'extra_sections': len(report.extra_sections),
                'out_of_order': len(report.out_of_order_sections)
            },
            'missing_sections': report.missing_sections,
            'extra_sections': report.extra_sections,
            'out_of_order_sections': report.out_of_order_sections,
            'discrepancies': [],
            'recommendations': []
        }
        
        # Add discrepancies
        if report.missing_sections:
            report_dict['discrepancies'].append(
                f"{len(report.missing_sections)} sections found in ToC but not in parsed content"
            )
        if report.extra_sections:
            report_dict['discrepancies'].append(
                f"{len(report.extra_sections)} sections found in parsed content but not in ToC"
            )
        
        # Add recommendations
        if report.match_percentage < 90:
            report_dict['recommendations'].append(
                "Review PDF structure and regex patterns for better matching"
            )
        if report.out_of_order_sections:
            report_dict['recommendations'].append(
                f"Check {len(report.out_of_order_sections)} out-of-order sections"
            )
        
        # Save report
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_dict, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Report saved to {output_path}")
        
        # Print summary
        print("\n" + "=" * 60)
        print("VALIDATION REPORT")
        print("=" * 60)
        print(f"ToC Sections: {report.toc_section_count}")
        print(f"Parsed Sections: {report.parsed_section_count}")
        print(f"Matched: {len(report.matched_sections)} ({report.match_percentage:.1f}%)")
        print(f"Missing: {len(report.missing_sections)}")
        print(f"Extra: {len(report.extra_sections)}")
        print(f"Out of Order: {len(report.out_of_order_sections)}")
        print("=" * 60)
        
        return report_dict


def main():
    """Run validation from command line."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate USB PD parsing results')
    parser.add_argument('toc_file', help='Path to ToC JSONL file')
    parser.add_argument('chunks_file', help='Path to chunks JSONL file')
    parser.add_argument('-o', '--output', default='validation_report.json',
                       help='Output report path')
    
    args = parser.parse_args()
    
    validator = TOCValidator()
    report = validator.validate(args.toc_file, args.chunks_file)
    validator.generate_report(report, args.output)


if __name__ == '__main__':
    main()