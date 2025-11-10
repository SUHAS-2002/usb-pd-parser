"""Unit tests for USB PD Parser."""
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Add parent directory to path
sys.path.insert(
    0,
    str(Path(__file__).parent.parent)
)

from usb_pd_parser import (
    USBPDParser,
    TOCEntry,
    AdvancedUSBPDParser,
    ContentChunk
)


class TestTOCEntry:
    """Tests for TOCEntry dataclass functionality."""

    def test_toc_entry_creation(self):
        """Test TOCEntry dataclass creation."""
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

    def test_to_dict(self):
        """Test TOCEntry to_dict conversion."""
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


class TestUSBPDParser:
    """Tests for USBPDParser functionality."""

    def test_calculate_level(self):
        """Test level calculation from section ID."""
        parser = USBPDParser()
        assert parser.calculate_level("2") == 1
        assert parser.calculate_level("2.1") == 2
        assert parser.calculate_level("2.1.3") == 3
        assert parser.calculate_level("4.3.2.1") == 4

    def test_get_parent_id(self):
        """Test parent ID extraction."""
        parser = USBPDParser()
        assert parser.get_parent_id("2") is None
        assert parser.get_parent_id("2.1") == "2"
        assert parser.get_parent_id("2.1.3") == "2.1"
        assert parser.get_parent_id("4.3.2.1") == "4.3.2"

    def test_parse_toc_line(self):
        """Test ToC line parsing."""
        parser = USBPDParser()
        line1 = (
            "2.1.2 Power Delivery Contract "
            "Negotiation ........... 53"
        )
        result1 = parser.parse_toc_line(line1)
        assert result1 is not None
        assert result1['section_id'] == "2.1.2"
        assert result1['page'] == 53
        assert "Power Delivery Contract Negotiation" in result1['title']

        line2 = "2.3 USB Power Delivery Capable Devices     55"
        result2 = parser.parse_toc_line(line2)
        assert result2 is not None
        assert result2['section_id'] == "2.3"
        assert result2['page'] == 55

    def test_generate_tags(self):
        """Test automatic tag generation."""
        parser = USBPDParser()
        tags1 = parser.generate_tags(
            "Power Delivery Contract Negotiation"
        )
        assert any(tag in tags1 for tag in ["contract", "power"])
        tags2 = parser.generate_tags(
            "USB Power Delivery Capable Devices"
        )
        assert "device" in tags2 or "power" in tags2
        tags3 = parser.generate_tags("Cable Plug Communication")
        assert "cable" in tags3 or "communication" in tags3

    def test_full_toc_parsing(self, tmp_path: Path):
        """Test end-to-end ToC file parsing."""
        toc_file = tmp_path / "toc.txt"
        toc_file.write_text(
            "1 Scope ........................................ 1\n"
            "2.1 Overview .................................. 12\n"
            "2.1.1 PD Messages ............................. 15\n",
            encoding="utf-8",
        )
        parser = USBPDParser()
        entries = parser.parse_toc_file(toc_file, doc_title="USB-PD Spec")
        assert len(entries) == 3
        assert entries[0].section_id == "1"
        assert entries[1].section_id == "2.1"
        assert entries[2].parent_id == "2.1"
        assert entries[2].level == 3


class TestAdvancedUSBPDParser:
    """Tests for AdvancedUSBPDParser functionality."""

    def test_advanced_parser_run(self, monkeypatch, tmp_path: Path):
        """Test AdvancedUSBPDParser with mocked PDF."""
        pdf_path = tmp_path / "spec.pdf"
        pdf_path.touch()
        fake_pages = [
            Mock(
                page_number=10,
                extract_text=lambda: (
                    "2.1 Overview of PD\nText\n"
                    "Figure 2-1: Diagram"
                )
            ),
            Mock(
                page_number=11,
                extract_text=lambda: (
                    "2.1.1 PD Messages\nMore\n"
                    "Table 2-1: Codes"
                )
            ),
        ]

        def fake_open(*_, **__):
            pdf = Mock()
            pdf.pages = fake_pages
            return pdf

        monkeypatch.setattr("pdfplumber.open", fake_open)
        parser = AdvancedUSBPDParser(str(pdf_path))
        chunks = parser.run(
            output_path=str(tmp_path / "out.jsonl"),
            start_page=10
        )
        assert len(chunks) == 2
        assert chunks[0].section_id == "2.1"
        assert "Figure 2-1: Diagram" in chunks[0].figures
        assert chunks[1].section_id == "2.1.1"
        assert "Table 2-1: Codes" in chunks[1].tables
        with open(tmp_path / "out.jsonl") as f:
            lines = f.readlines()
            assert len(lines) == 2
            data = json.loads(lines[0])
            assert data["section_id"] == "2.1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])