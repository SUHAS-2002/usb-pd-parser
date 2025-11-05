#!/usr/bin/env python3
"""
USB Power Delivery Specification Parser - Full Document Version
================================================================
Extracts Table of Contents and COMPLETE content from large USB PD PDFs (1000+ pages)

Key Features:
- Scans entire PDF for ToC entries
- Extracts all content without page limits
- Memory-efficient chunked processing
- Robust section boundary detection

Version: 3.0 - Full PDF Support
"""

import re
import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
import pdfplumber
from collections import defaultdict

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TOCEntry:
    """Table of Contents entry with full metadata."""
    doc_title: str
    section_id: str
    title: str
    full_path: str
    page: int
    level: int
    parent_id: Optional[str]
    tags: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ContentChunk:
    """Represents a parsed content section."""
    doc_title: str
    section_id: str
    section_path: str
    start_heading: str
    start_page: int
    end_page: int
    content: str
    subsections: List[str] = field(default_factory=list)
    tables: List[Dict] = field(default_factory=list)
    figures: List[Dict] = field(default_factory=list)
    word_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class USBPDParser:
    """Enhanced parser for complete USB PD specification extraction."""
    
    TOC_PATTERNS = [
        r'^(\d+(?:\.\d+)*)\s+([^\.\d][^\n]+?)\s*\.{2,}\s*(\d+)\s*$',
        r'^(\d+(?:\.\d+)*)\s+([^\.\d][^\n]+?)\s{3,}(\d+)\s*$',
        r'^(\d+(?:\.\d+)*)\s+([^\.\d].+?)\s+(\d+)\s*$',
        r'^(\d+(?:\.\d+)*)\s*[:\-]\s*([^\n]+?)\s*\.{2,}\s*(\d+)\s*$',
    ]
    
    SECTION_PATTERNS = [
        r'^(\d+(?:\.\d+)*)\s+([A-Z][^\n]{3,100})$',
        r'^(\d+(?:\.\d+)*)\s*[:\-]\s*([A-Z][^\n]{3,100})$',
        r'^Section\s+(\d+(?:\.\d+)*)[:\s]+([^\n]{3,100})$',
    ]
    
    def __init__(self, pdf_path: str, doc_title: str = "USB Power Delivery Specification"):
        self.pdf_path = Path(pdf_path)
        self.doc_title = doc_title
        self.toc_entries: List[TOCEntry] = []
        self.content_chunks: List[ContentChunk] = []
        self.toc_page_map: Dict[str, int] = {}
        self.total_pdf_pages: int = 0
        
        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    def get_pdf_page_count(self) -> int:
        """Get total page count from PDF."""
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                return len(pdf.pages)
        except Exception as e:
            logger.error(f"Error reading PDF: {e}")
            return 0
    
    def extract_toc_pages(self, scan_all: bool = True) -> Tuple[str, List[int]]:
        """
        Extract text from ToC pages - scans entire PDF by default.
        
        Args:
            scan_all: If True, scans all pages for ToC entries (recommended)
        """
        logger.info(f"Opening PDF: {self.pdf_path}")
        toc_text = ""
        toc_pages = []
        
        try:
            with pdfplumber.open(self.pdf_path) as pdf:
                self.total_pdf_pages = len(pdf.pages)
                logger.info(f"Total pages in PDF: {self.total_pdf_pages}")
                
                # Scan either all pages or first 50
                max_scan = self.total_pdf_pages if scan_all else min(50, self.total_pdf_pages)
                logger.info(f"Scanning first {max_scan} pages for ToC...")
                
                for i in range(max_scan):
                    if i % 10 == 0:
                        logger.info(f"  Scanning page {i+1}/{max_scan}...")
                    
                    page = pdf.pages[i]
                    text = page.extract_text() or ""
                    
                    # Check if page contains ToC indicators OR section numbers
                    has_toc_indicators = any(indicator in text.lower() for indicator in 
                                            ['table of contents', 'contents'])
                    has_section_numbers = bool(re.search(r'^\d+(?:\.\d+)+\s+', text, re.MULTILINE))
                    
                    if has_toc_indicators or has_section_numbers:
                        toc_text += text + "\n"
                        toc_pages.append(i + 1)
                        
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise
        
        logger.info(f"Extracted ToC from {len(toc_pages)} pages")
        return toc_text, toc_pages
    
    def parse_toc_line(self, line: str) -> Optional[Dict[str, Any]]:
        """Parse a single ToC line."""
        line = line.strip()
        
        if not line or len(line) < 5:
            return None
        
        for pattern in self.TOC_PATTERNS:
            match = re.match(pattern, line)
            if match:
                section_id = match.group(1).strip()
                title = match.group(2).strip()
                page = match.group(3).strip()
                
                # Clean title
                title = re.sub(r'\.{2,}', '', title).strip()
                title = re.sub(r'\s{2,}', ' ', title).strip()
                title = title.rstrip('.')
                
                if not re.match(r'^\d+(\.\d+)*$', section_id):
                    continue
                
                try:
                    page_num = int(page)
                    if page_num < 1 or page_num > 10000:
                        continue
                except ValueError:
                    continue
                
                return {
                    'section_id': section_id,
                    'title': title,
                    'page': page_num
                }
        
        return None
    
    def calculate_level(self, section_id: str) -> int:
        """Calculate hierarchy level from section ID."""
        return len(section_id.split('.'))
    
    def get_parent_id(self, section_id: str) -> Optional[str]:
        """Get parent section ID."""
        parts = section_id.split('.')
        if len(parts) <= 1:
            return None
        return '.'.join(parts[:-1])
    
    def generate_tags(self, title: str) -> List[str]:
        """Generate semantic tags."""
        keywords = {
            'contract': ['contract', 'negotiation', 'agreement', 'capability'],
            'communication': ['communication', 'message', 'protocol', 'data'],
            'device': ['device', 'source', 'sink', 'drp', 'port'],
            'power': ['power', 'voltage', 'current', 'vbus', 'supply'],
            'cable': ['cable', 'plug', 'connector', 'wire'],
            'collision': ['collision', 'avoidance', 'detect'],
            'revision': ['revision', 'compatibility', 'version', 'legacy'],
            'requirements': ['requirement', 'shall', 'must', 'mandatory'],
            'testing': ['test', 'validation', 'verification', 'compliance'],
            'state': ['state', 'machine', 'transition', 'mode'],
        }
        
        tags = []
        title_lower = title.lower()
        
        for tag, terms in keywords.items():
            if any(term in title_lower for term in terms):
                tags.append(tag)
        
        return tags
    
    def build_full_path(self, section_id: str, title: str) -> str:
        """Build hierarchical path for section."""
        return f"{section_id} {title}"
    
    def parse_toc(self, toc_text: str) -> List[TOCEntry]:
        """Parse entire ToC with validation."""
        logger.info("Parsing Table of Contents...")
        entries = []
        seen_sections = set()
        lines = toc_text.split('\n')
        
        for line in lines:
            parsed = self.parse_toc_line(line)
            
            if parsed:
                section_id = parsed['section_id']
                
                if section_id in seen_sections:
                    continue
                
                seen_sections.add(section_id)
                title = parsed['title']
                page = parsed['page']
                
                entry = TOCEntry(
                    doc_title=self.doc_title,
                    section_id=section_id,
                    title=title,
                    full_path=self.build_full_path(section_id, title),
                    page=page,
                    level=self.calculate_level(section_id),
                    parent_id=self.get_parent_id(section_id),
                    tags=self.generate_tags(title)
                )
                
                entries.append(entry)
                self.toc_page_map[section_id] = page
        
        entries.sort(key=lambda x: [int(p) for p in x.section_id.split('.')])
        
        logger.info(f"Successfully parsed {len(entries)} unique ToC entries")
        return entries
    
    def extract_full_content(self, batch_size: int = 50) -> None:
        """
        Extract COMPLETE content from entire PDF using batched processing.
        
        Args:
            batch_size: Number of pages to process at once (memory optimization)
        """
        logger.info("Extracting FULL document content from ALL pages...")
        
        if not self.toc_entries:
            logger.warning("No ToC entries found. Run parse_toc first.")
            return
        
        if not self.total_pdf_pages:
            self.total_pdf_pages = self.get_pdf_page_count()
        
        logger.info(f"Processing ALL {self.total_pdf_pages} pages...")
        
        try:
            # Build comprehensive section boundaries
            section_pages = self._build_complete_section_boundaries()
            
            with pdfplumber.open(self.pdf_path) as pdf:
                # Process each section
                for idx, entry in enumerate(self.toc_entries, 1):
                    section_id = entry.section_id
                    start_pg, end_pg = section_pages.get(section_id, (entry.page, entry.page))
                    
                    # Log progress
                    if idx % 10 == 0:
                        logger.info(f"  Processing section {idx}/{len(self.toc_entries)}: {section_id}")
                    
                    # Extract content for this section
                    content = self._extract_section_content_batched(
                        pdf, start_pg, end_pg, batch_size
                    )
                    
                    if content:
                        chunk = ContentChunk(
                            doc_title=self.doc_title,
                            section_id=section_id,
                            section_path=entry.full_path,
                            start_heading=entry.title,
                            start_page=start_pg,
                            end_page=end_pg,
                            content=content,
                            subsections=self._find_subsections(section_id),
                            word_count=len(content.split())
                        )
                        
                        self.content_chunks.append(chunk)
                
                logger.info(f"✓ Extracted {len(self.content_chunks)} content sections from ENTIRE PDF")
                
        except Exception as e:
            logger.error(f"Error extracting content: {e}")
            raise
    
    def _build_complete_section_boundaries(self) -> Dict[str, Tuple[int, int]]:
        """
        Build COMPLETE start/end page boundaries for ALL sections.
        Uses actual PDF length instead of arbitrary limits.
        """
        boundaries = {}
        sorted_entries = sorted(self.toc_entries, key=lambda x: x.page)
        
        for i, entry in enumerate(sorted_entries):
            start_page = entry.page
            
            # Find next section at same or higher level
            end_page = self.total_pdf_pages  # Default to end of PDF
            
            for next_entry in sorted_entries[i+1:]:
                if next_entry.level <= entry.level:
                    end_page = next_entry.page - 1
                    break
            
            # Ensure we don't exceed PDF bounds
            end_page = min(end_page, self.total_pdf_pages)
            
            boundaries[entry.section_id] = (start_page, end_page)
            
            logger.debug(f"Section {entry.section_id}: pages {start_page}-{end_page}")
        
        return boundaries
    
    def _extract_section_content_batched(self, pdf, start_page: int, 
                                        end_page: int, batch_size: int) -> str:
        """
        Extract content from page range using batched processing.
        Memory-efficient for large page ranges.
        """
        content_parts = []
        
        start_idx = max(0, start_page - 1)
        end_idx = min(len(pdf.pages), end_page)
        
        # Process in batches
        for batch_start in range(start_idx, end_idx, batch_size):
            batch_end = min(batch_start + batch_size, end_idx)
            
            for page_num in range(batch_start, batch_end):
                if page_num >= len(pdf.pages):
                    break
                
                page = pdf.pages[page_num]
                text = page.extract_text() or ""
                
                text = self._clean_content_text(text)
                if text.strip():  # Only add non-empty content
                    content_parts.append(text)
        
        return "\n\n".join(content_parts)
    
    def _clean_content_text(self, text: str) -> str:
        """Clean extracted text content."""
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            # Skip page numbers, headers, footers
            if re.match(r'^\s*\d+\s*$', line):
                continue
            if re.match(r'^Page \d+ of \d+', line, re.IGNORECASE):
                continue
            if re.match(r'^\s*USB Power Delivery', line, re.IGNORECASE):
                continue
            if len(line.strip()) > 0:
                cleaned_lines.append(line)
        
        return '\n'.join(cleaned_lines)
    
    def _find_subsections(self, section_id: str) -> List[str]:
        """Find immediate subsections."""
        subsections = []
        for entry in self.toc_entries:
            if entry.parent_id == section_id:
                subsections.append(entry.section_id)
        return subsections
    
    def save_toc_jsonl(self, output_path: str) -> None:
        """Save ToC entries to JSONL."""
        output_file = Path(output_path)
        logger.info(f"Writing ToC to: {output_file}")
        
        try:
            with output_file.open('w', encoding='utf-8') as f:
                for entry in self.toc_entries:
                    json_line = json.dumps(entry.to_dict(), ensure_ascii=False)
                    f.write(json_line + '\n')
            
            logger.info(f"✓ Wrote {len(self.toc_entries)} ToC entries")
        except Exception as e:
            logger.error(f"Error writing ToC JSONL: {e}")
            raise
    
    def save_content_jsonl(self, output_path: str) -> None:
        """Save content chunks to JSONL."""
        output_file = Path(output_path)
        logger.info(f"Writing content to: {output_file}")
        
        try:
            with output_file.open('w', encoding='utf-8') as f:
                for chunk in self.content_chunks:
                    json_line = json.dumps(chunk.to_dict(), ensure_ascii=False)
                    f.write(json_line + '\n')
            
            logger.info(f"✓ Wrote {len(self.content_chunks)} content chunks")
            
            # Calculate total content size
            total_words = sum(c.word_count for c in self.content_chunks)
            logger.info(f"✓ Total content: {total_words:,} words extracted")
            
        except Exception as e:
            logger.error(f"Error writing content JSONL: {e}")
            raise
    
    def generate_statistics(self) -> Dict[str, Any]:
        """Generate comprehensive parsing statistics."""
        stats = {
            'pdf_info': {
                'total_pages': self.total_pdf_pages,
                'file_path': str(self.pdf_path)
            },
            'toc_statistics': {
                'total_entries': len(self.toc_entries),
                'by_level': defaultdict(int),
                'page_range': {
                    'min': min((e.page for e in self.toc_entries), default=0),
                    'max': max((e.page for e in self.toc_entries), default=0)
                }
            },
            'content_statistics': {
                'total_chunks': len(self.content_chunks),
                'total_words': sum(c.word_count for c in self.content_chunks),
                'avg_words_per_section': 0,
                'coverage_percentage': 0,
                'pages_covered': 0
            }
        }
        
        for entry in self.toc_entries:
            stats['toc_statistics']['by_level'][entry.level] += 1
        
        if self.content_chunks:
            stats['content_statistics']['avg_words_per_section'] = (
                stats['content_statistics']['total_words'] / len(self.content_chunks)
            )
            
            # Calculate pages covered
            pages_covered = set()
            for chunk in self.content_chunks:
                pages_covered.update(range(chunk.start_page, chunk.end_page + 1))
            stats['content_statistics']['pages_covered'] = len(pages_covered)
        
        if self.toc_entries:
            stats['content_statistics']['coverage_percentage'] = (
                len(self.content_chunks) / len(self.toc_entries) * 100
            )
        
        return stats
    
    def run(self, output_toc: str = "usb_pd_toc.jsonl",
            output_content: str = "usb_pd_content.jsonl",
            extract_content: bool = True,
            scan_all_toc: bool = True,
            batch_size: int = 50) -> Dict[str, Any]:
        """
        Run complete parsing pipeline for ENTIRE PDF.
        
        Args:
            output_toc: Output file for ToC
            output_content: Output file for content
            extract_content: Whether to extract full content
            scan_all_toc: Scan all pages for ToC (True = comprehensive)
            batch_size: Pages to process at once (memory optimization)
        """
        logger.info("=" * 70)
        logger.info("USB PD Parser v3.0 - FULL PDF EXTRACTION")
        logger.info("=" * 70)
        
        # Get PDF info
        self.total_pdf_pages = self.get_pdf_page_count()
        logger.info(f"PDF has {self.total_pdf_pages} total pages")
        
        # Extract and parse ToC
        toc_text, toc_pages = self.extract_toc_pages(scan_all=scan_all_toc)
        self.toc_entries = self.parse_toc(toc_text)
        
        if not self.toc_entries:
            logger.error("❌ No ToC entries found! Check PDF format.")
            return {}
        
        # Save ToC
        self.save_toc_jsonl(output_toc)
        
        # Extract COMPLETE content
        if extract_content:
            self.extract_full_content(batch_size=batch_size)
            self.save_content_jsonl(output_content)
        
        # Generate statistics
        stats = self.generate_statistics()
        self._display_summary(stats)
        
        logger.info("=" * 70)
        logger.info("✓ COMPLETE PARSING FINISHED!")
        logger.info("=" * 70)
        
        return stats
    
    def _display_summary(self, stats: Dict[str, Any]) -> None:
        """Display comprehensive parsing summary."""
        logger.info("\n" + "=" * 70)
        logger.info("COMPLETE PARSING SUMMARY")
        logger.info("=" * 70)
        
        pdf_info = stats['pdf_info']
        logger.info(f"PDF: {pdf_info['total_pages']} total pages")
        
        toc_stats = stats['toc_statistics']
        logger.info(f"\nToC Entries: {toc_stats['total_entries']}")
        logger.info(f"Page Range: {toc_stats['page_range']['min']} - "
                   f"{toc_stats['page_range']['max']}")
        logger.info("Entries by Level:")
        for level, count in sorted(toc_stats['by_level'].items()):
            logger.info(f"  Level {level}: {count} sections")
        
        if stats['content_statistics']['total_chunks'] > 0:
            content_stats = stats['content_statistics']
            logger.info(f"\nContent Extraction:")
            logger.info(f"  Sections Extracted: {content_stats['total_chunks']}")
            logger.info(f"  Total Words: {content_stats['total_words']:,}")
            logger.info(f"  Pages Covered: {content_stats['pages_covered']}/{pdf_info['total_pages']}")
            logger.info(f"  Avg Words/Section: {content_stats['avg_words_per_section']:.0f}")
            logger.info(f"  Coverage: {content_stats['coverage_percentage']:.1f}%")


def main():
    """Main entry point with full PDF support."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='USB PD Parser v3.0 - COMPLETE PDF Extraction (1000+ pages)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract COMPLETE PDF (recommended)
  %(prog)s spec.pdf --extract-content
  
  # Extract with custom batch size for memory optimization
  %(prog)s spec.pdf --extract-content --batch-size 100
  
  # ToC only (fast preview)
  %(prog)s spec.pdf -o toc.jsonl
        """
    )
    
    parser.add_argument('pdf_path', help='Path to USB PD specification PDF')
    parser.add_argument('-o', '--output-toc', default='usb_pd_toc.jsonl',
                       help='Output ToC JSONL file')
    parser.add_argument('-c', '--output-content', default='usb_pd_content.jsonl',
                       help='Output content JSONL file')
    parser.add_argument('-t', '--title', 
                       default='USB Power Delivery Specification',
                       help='Document title')
    parser.add_argument('--extract-content', action='store_true',
                       help='Extract COMPLETE document content (all pages)')
    parser.add_argument('--batch-size', type=int, default=50,
                       help='Pages per batch (default: 50, higher = faster but more memory)')
    parser.add_argument('--no-scan-all-toc', action='store_true',
                       help='Only scan first 50 pages for ToC (faster but may miss entries)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Enable verbose debug logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        pd_parser = USBPDParser(args.pdf_path, args.title)
        stats = pd_parser.run(
            output_toc=args.output_toc,
            output_content=args.output_content,
            extract_content=args.extract_content,
            scan_all_toc=not args.no_scan_all_toc,
            batch_size=args.batch_size
        )
        
        return 0
        
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=args.verbose)
        return 1


if __name__ == '__main__':
    exit(main())