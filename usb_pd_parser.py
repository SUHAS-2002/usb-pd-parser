#!/usr/bin/env python3
"""
USB Power Delivery Specification Parser
========================================
Extracts Table of Contents from USB PD PDF specifications and generates
structured JSONL output with hierarchical section information.

Author: Assignment Solution
Date: 2025
"""

import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
import pdfplumber

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TOCEntry:
    """Represents a single Table of Contents entry."""
    doc_title: str
    section_id: str
    title: str
    full_path: str
    page: int
    level: int
    parent_id: Optional[str]
    tags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSONL output."""
        return asdict(self)


class USBPDParser:
    """Parser for USB Power Delivery specification PDFs."""
    
    # Regex patterns for ToC extraction
    TOC_PATTERNS = [
        # Pattern 1: "2.1.2 Title ........... 53"
        r'^(\d+(?:\.\d+)*)\s+([^\.\d][^\n]+?)\s*\.{2,}\s*(\d+)\s*$',
        # Pattern 2: "2.1.2 Title    53"
        r'^(\d+(?:\.\d+)*)\s+([^\.\d][^\n]+?)\s{3,}(\d+)\s*$',
        # Pattern 3: "2.1.2 Title 53" (less whitespace)
        r'^(\d+(?:\.\d+)*)\s+([^\.\d].+?)\s+(\d+)\s*$',
    ]
    
    def __init__(self, pdf_path: str, doc_title: str = "USB Power Delivery Specification Rev X"):
        """
        Initialize the parser.
        
        Args:
            pdf_path: Path to the PDF file
            doc_title: Title of the document
        """
        self.pdf_path = Path(pdf_path)
        self.doc_title = doc_title
        self.toc_entries: List[TOCEntry] = []
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    def extract_toc_text(self, max_pages: int = 15) -> str:
        """
        Extract text from the front matter pages containing ToC.
        
        Args:
            max_pages: Maximum number of pages to scan for ToC
            
        Returns:
            Extracted text from ToC pages
        """
        logger.info(f"Opening PDF: {self.pdf_path}")
        toc_text = ""
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                logger.info(f"Total pages in PDF: {len(pdf.pages)}")
                
                # Scan first pages for ToC
                for i, page in enumerate(pdf.pages[:max_pages]):
                    text = page.extract_text()
                    if text:
                        toc_text += text + "\n"
                        logger.debug(f"Extracted text from page {i+1}")
                        
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise
        
        return toc_text
    
    def parse_toc_line(self, line: str) -> Optional[Dict[str, str]]:
        """
        Parse a single ToC line using regex patterns.
        
        Args:
            line: Single line from ToC
            
        Returns:
            Dictionary with section_id, title, page or None
        """
        line = line.strip()
        
        # Try each pattern
        for pattern in self.TOC_PATTERNS:
            match = re.match(pattern, line)
            if match:
                section_id = match.group(1).strip()
                title = match.group(2).strip()
                page = match.group(3).strip()
                
                # Clean up title (remove extra dots and spaces)
                title = re.sub(r'\.{2,}', '', title).strip()
                title = re.sub(r'\s{2,}', ' ', title).strip()
                
                return {
                    'section_id': section_id,
                    'title': title,
                    'page': int(page)
                }
        
        return None
    
    def calculate_level(self, section_id: str) -> int:
        """
        Calculate hierarchy level from section ID.
        
        Args:
            section_id: Section identifier (e.g., "2.1.2")
            
        Returns:
            Hierarchy level (1 for "2", 2 for "2.1", 3 for "2.1.2")
        """
        return len(section_id.split('.'))
    
    def get_parent_id(self, section_id: str) -> Optional[str]:
        """
        Get parent section ID.
        
        Args:
            section_id: Section identifier (e.g., "2.1.2")
            
        Returns:
            Parent section ID (e.g., "2.1") or None for top level
        """
        parts = section_id.split('.')
        if len(parts) <= 1:
            return None
        return '.'.join(parts[:-1])
    
    def generate_tags(self, title: str) -> List[str]:
        """
        Generate semantic tags from title.
        
        Args:
            title: Section title
            
        Returns:
            List of tags
        """
        keywords = {
            'contract': ['contract', 'negotiation', 'agreement'],
            'communication': ['communication', 'message', 'protocol'],
            'device': ['device', 'source', 'sink', 'drp'],
            'power': ['power', 'voltage', 'current', 'vbus'],
            'cable': ['cable', 'plug', 'connector'],
            'collision': ['collision', 'avoidance'],
            'revision': ['revision', 'compatibility', 'version'],
        }
        
        tags = []
        title_lower = title.lower()
        
        for tag, terms in keywords.items():
            if any(term in title_lower for term in terms):
                tags.append(tag)
        
        return tags
    
    def parse_toc(self, toc_text: str) -> List[TOCEntry]:
        """
        Parse entire ToC text into structured entries.
        
        Args:
            toc_text: Raw ToC text
            
        Returns:
            List of TOCEntry objects
        """
        logger.info("Parsing Table of Contents...")
        entries = []
        lines = toc_text.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            parsed = self.parse_toc_line(line)
            
            if parsed:
                section_id = parsed['section_id']
                title = parsed['title']
                page = parsed['page']
                
                entry = TOCEntry(
                    doc_title=self.doc_title,
                    section_id=section_id,
                    title=title,
                    full_path=f"{section_id} {title}",
                    page=page,
                    level=self.calculate_level(section_id),
                    parent_id=self.get_parent_id(section_id),
                    tags=self.generate_tags(title)
                )
                
                entries.append(entry)
                logger.debug(f"Parsed: {entry.full_path}")
        
        logger.info(f"Successfully parsed {len(entries)} ToC entries")
        return entries
    
    def save_to_jsonl(self, output_path: str):
        """
        Save parsed entries to JSONL file.
        
        Args:
            output_path: Output file path
        """
        output_file = Path(output_path)
        logger.info(f"Writing JSONL to: {output_file}")
        
        try:
            with output_file.open('w', encoding='utf-8') as f:
                for entry in self.toc_entries:
                    json_line = json.dumps(entry.to_dict(), ensure_ascii=False)
                    f.write(json_line + '\n')
            
            logger.info(f"Successfully wrote {len(self.toc_entries)} entries to {output_file}")
        except Exception as e:
            logger.error(f"Error writing JSONL: {e}")
            raise
    
    def generate_statistics(self) -> Dict[str, Any]:
        """Generate statistics about parsed ToC."""
        stats = {
            'total_entries': len(self.toc_entries),
            'by_level': {},
            'page_range': {
                'min': min((e.page for e in self.toc_entries), default=0),
                'max': max((e.page for e in self.toc_entries), default=0)
            },
            'sections_by_level': {}
        }
        
        for entry in self.toc_entries:
            level = entry.level
            stats['by_level'][level] = stats['by_level'].get(level, 0) + 1
        
        return stats
    
    def run(self, output_path: str = "usb_pd_spec.jsonl", max_toc_pages: int = 15):
        """
        Run the complete parsing pipeline.
        
        Args:
            output_path: Output JSONL file path
            max_toc_pages: Maximum pages to scan for ToC
        """
        logger.info("=" * 60)
        logger.info("USB PD Specification Parser - Starting")
        logger.info("=" * 60)
        
        # Extract ToC text
        toc_text = self.extract_toc_text(max_pages=max_toc_pages)
        
        # Parse ToC
        self.toc_entries = self.parse_toc(toc_text)
        
        if not self.toc_entries:
            logger.warning("No ToC entries found! Check PDF format and regex patterns.")
            return
        
        # Save to JSONL
        self.save_to_jsonl(output_path)
        
        # Generate and display statistics
        stats = self.generate_statistics()
        logger.info("\n" + "=" * 60)
        logger.info("Parsing Statistics:")
        logger.info(f"  Total entries: {stats['total_entries']}")
        logger.info(f"  Page range: {stats['page_range']['min']} - {stats['page_range']['max']}")
        logger.info("  Entries by level:")
        for level, count in sorted(stats['by_level'].items()):
            logger.info(f"    Level {level}: {count} entries")
        logger.info("=" * 60)
        logger.info("✓ Parsing complete!")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Parse USB PD Specification PDF and extract Table of Contents'
    )
    parser.add_argument(
        'pdf_path',
        help='Path to the USB PD specification PDF file'
    )
    parser.add_argument(
        '-o', '--output',
        default='usb_pd_spec.jsonl',
        help='Output JSONL file path (default: usb_pd_spec.jsonl)'
    )
    parser.add_argument(
        '-t', '--title',
        default='USB Power Delivery Specification Rev X',
        help='Document title for metadata'
    )
    parser.add_argument(
        '-p', '--pages',
        type=int,
        default=15,
        help='Maximum pages to scan for ToC (default: 15)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Initialize and run parser
        pd_parser = USBPDParser(args.pdf_path, args.title)
        pd_parser.run(args.output, args.pages)
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())