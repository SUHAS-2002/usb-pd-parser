"""Unit tests for USB PD Parser"""
import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from usb_pd_parser import USBPDParser, TOCEntry


def test_toc_entry_creation():
    """Test TOCEntry dataclass creation"""
    entry = TOCEntry(
        doc_title="Test Doc",
        section_id="2.1",
        title="Test Section",
        full_path="2.1 Test Section",
        page=10,
        level=2,
        parent_id="2",
        tags=["test"]
    )
    assert entry.section_id == "2.1"
    assert entry.level == 2
    assert entry.page == 10


def test_calculate_level():
    """Test level calculation from section ID"""
    parser = USBPDParser.__new__(USBPDParser)
    assert parser.calculate_level("2") == 1
    assert parser.calculate_level("2.1") == 2
    assert parser.calculate_level("2.1.3") == 3
    assert parser.calculate_level("4.3.2.1") == 4


def test_get_parent_id():
    """Test parent ID extraction"""
    parser = USBPDParser.__new__(USBPDParser)
    assert parser.get_parent_id("2") is None
    assert parser.get_parent_id("2.1") == "2"
    assert parser.get_parent_id("2.1.3") == "2.1"
    assert parser.get_parent_id("4.3.2.1") == "4.3.2"


def test_parse_toc_line():
    """Test ToC line parsing"""
    parser = USBPDParser.__new__(USBPDParser)
    parser.TOC_PATTERNS = USBPDParser.TOC_PATTERNS
    
    # Test different formats
    line1 = "2.1.2 Power Delivery Contract Negotiation ........... 53"
    result1 = parser.parse_toc_line(line1)
    assert result1 is not None
    assert result1['section_id'] == "2.1.2"
    assert result1['page'] == 53
    assert "Power Delivery Contract Negotiation" in result1['title']
    
    # Test format with less dots
    line2 = "2.3 USB Power Delivery Capable Devices     55"
    result2 = parser.parse_toc_line(line2)
    assert result2 is not None
    assert result2['section_id'] == "2.3"
    assert result2['page'] == 55


def test_generate_tags():
    """Test automatic tag generation"""
    parser = USBPDParser.__new__(USBPDParser)
    parser.generate_tags = USBPDParser.generate_tags.__get__(parser)
    
    tags1 = parser.generate_tags("Power Delivery Contract Negotiation")
    assert any(tag in tags1 for tag in ["contract", "power"])
    
    tags2 = parser.generate_tags("USB Power Delivery Capable Devices")
    assert "device" in tags2 or "power" in tags2
    
    tags3 = parser.generate_tags("Cable Plug Communication")
    assert "cable" in tags3 or "communication" in tags3


def test_to_dict():
    """Test TOCEntry to_dict conversion"""
    entry = TOCEntry(
        doc_title="Test Doc",
        section_id="2.1",
        title="Test Section",
        full_path="2.1 Test Section",
        page=10,
        level=2,
        parent_id="2",
        tags=["test"]
    )
    
    entry_dict = entry.to_dict()
    assert isinstance(entry_dict, dict)
    assert entry_dict['section_id'] == "2.1"
    assert entry_dict['level'] == 2
    assert entry_dict['tags'] == ["test"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])