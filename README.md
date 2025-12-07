# USB Power Delivery (USB PD) Specification Parser

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A high-fidelity parsing system for USB Power Delivery specification PDFs that extracts structured content, preserves hierarchical relationships, and generates machine-readable JSONL output.

## 📋 Overview

This project converts complex USB PD specification PDFs into structured, machine-readable formats (JSONL) while preserving:
- **Table of Contents (ToC)** hierarchy with page numbers
- **Section relationships** (chapters, subsections)
- **Metadata** (figures, tables, protocol descriptions)
- **Validation reports** comparing parsed structure against ToC

## 🎯 Features

- ✅ **Multi-strategy ToC extraction** using regex patterns
- ✅ **High-fidelity content parsing** with PyMuPDF and pdfplumber
- ✅ **Hierarchical section building** preserving document structure
- ✅ **JSON schema validation** for ToC and content
- ✅ **Comprehensive validation reports** (JSON + Excel)
- ✅ **CLI interface** for easy execution
- ✅ **Metadata generation** with document statistics

## 📦 Project Structure

```
usb-pd-parser/
├── data/                           # Output directory
│   ├── usb_pd_toc.jsonl           # Table of Contents
│   ├── usb_pd_content.jsonl       # Section content
│   ├── usb_pd_spec.jsonl          # Combined specification
│   ├── usb_pd_metadata.jsonl      # Document metadata
│   ├── validation_report.json     # Validation results
│   └── validation_report.xlsx     # Excel report
│
├── src/
│   ├── extractors/
│   │   ├── high_fidelity_extractor.py   # PDF text extraction
│   │   ├── toc_extractor.py             # ToC parsing
│   │   └── section_builder.py           # Section hierarchy builder
│   │
│   ├── validator/
│   │   ├── toc_validator.py             # ToC validation
│   │   ├── matcher.py                   # Title/page matching
│   │   └── report_generator.py          # Report generation
│   │
│   ├── generators/
│   │   ├── spec_jsonl_generator.py      # Final JSONL builder
│   │   └── metadata_generator.py        # Statistics generator
│   │
│   ├── schemas/
│   │   ├── toc_schema.json              # ToC JSON schema
│   │   └── content_schema.json          # Content JSON schema
│   │
│   └── usb_pd_parser.py                 # Main orchestrator
│
├── requirements.txt                     # Python dependencies
├── setup_and_run.bat                    # Windows setup script
├── setup_and_run.sh                     # Linux/Mac setup script
└── README.md                            # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

#### Windows

```bash
# Run the automated setup script
setup_and_run.bat
```

#### Linux/Mac

```bash
# Make the script executable
chmod +x setup_and_run.sh

# Run the setup script
./setup_and_run.sh
```

#### Manual Installation

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 💻 Usage

### Basic Usage

```bash
# Parse a USB PD specification PDF
python src/usb_pd_parser.py data/usb_pd_spec.pdf
```

### CLI Options

```bash
# Full command with all options
python src/usb_pd_parser.py <pdf_path> [options]

Options:
  --output-dir DIR      Output directory (default: data/)
  --validate           Generate validation report
  --skip-toc           Skip ToC extraction
  --verbose            Enable detailed logging
```

### Using the CLI Interface

```bash
# Using the CLI module
python -m src.usbpd.cli parse data/usb_pd_spec.pdf

# Validate existing output
python -m src.usbpd.cli validate --toc data/usb_pd_toc.jsonl --content data/usb_pd_content.jsonl
```

## 📄 Output Files

### 1. `usb_pd_toc.jsonl`
Table of Contents with hierarchical structure:
```json
{
  "section_number": "1.2.3",
  "title": "Protocol Layer",
  "page_number": 45,
  "level": 3,
  "parent_section": "1.2"
}
```

### 2. `usb_pd_content.jsonl`
Extracted section content:
```json
{
  "section_number": "1.2.3",
  "title": "Protocol Layer",
  "content": "The Protocol Layer handles...",
  "page_start": 45,
  "page_end": 47,
  "figures": ["Figure 1-5", "Figure 1-6"],
  "tables": ["Table 1-3"]
}
```

### 3. `usb_pd_spec.jsonl`
Combined specification (ToC + content merged)

### 4. `usb_pd_metadata.jsonl`
Document statistics and metadata

### 5. `validation_report.json` / `validation_report.xlsx`
Validation results comparing ToC against parsed content:
- Total sections in ToC vs parsed
- Matching sections
- Mismatches and gaps
- Order errors
- Quality score

## 🏗️ Architecture

### Core Components

1. **Extractors**
   - `high_fidelity_extractor.py`: Combines PyMuPDF text extraction with pdfplumber for tables
   - `toc_extractor.py`: Multi-regex pattern matching for ToC extraction
   - `section_builder.py`: Builds hierarchical section structure from ToC

2. **Validators**
   - `toc_validator.py`: Validates ToC completeness and accuracy
   - `matcher.py`: Fuzzy matching engine for title/page alignment
   - `report_generator.py`: Generates comprehensive validation reports

3. **Generators**
   - `spec_jsonl_generator.py`: Merges ToC and content into final output
   - `metadata_generator.py`: Extracts document statistics

### Processing Pipeline

```
PDF Input
    ↓
[ToC Extraction] → usb_pd_toc.jsonl
    ↓
[Content Extraction] → usb_pd_content.jsonl
    ↓
[Section Building] → Hierarchical structure
    ↓
[Validation] → validation_report.json/xlsx
    ↓
[Final Generation] → usb_pd_spec.jsonl + usb_pd_metadata.jsonl
```

## 📊 Validation Metrics

The validation report includes:

- **Total Sections**: ToC count vs parsed count
- **Match Rate**: Percentage of correctly matched sections
- **Mismatches**: Sections with title/page discrepancies
- **Gaps**: Missing sections in parsed output
- **Order Errors**: Sections appearing in wrong sequence
- **Quality Score**: Overall parsing accuracy (0-100)

## 🔧 Configuration

### JSON Schemas

Validation schemas are defined in `src/schemas/`:
- `toc_schema.json`: Defines ToC entry structure
- `content_schema.json`: Defines section content structure

### Customization

Modify extraction parameters in the source files:
- ToC regex patterns: `src/extractors/toc_extractor.py`
- Content extraction settings: `src/extractors/high_fidelity_extractor.py`
- Validation thresholds: `src/validator/toc_validator.py`

## 🧪 Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test
pytest tests/test_toc_extractor.py
```

## 📝 Example JSONL Output

Sample output files are provided in the `examples/` directory:
- `examples/usb_pd_toc.jsonl` - Sample ToC output
- `examples/usb_pd_spec.jsonl` - Sample specification output
- `examples/usb_pd_metadata.jsonl` - Sample metadata output

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🐛 Troubleshooting

### Common Issues

**Issue**: PDF not found
```
Solution: Ensure the PDF path is correct and the file exists
```

**Issue**: Empty ToC extraction
```
Solution: Check if the PDF has a proper Table of Contents section
         Try adjusting regex patterns in toc_extractor.py
```

**Issue**: Memory errors with large PDFs
```
Solution: Process PDFs in chunks or increase available memory
```

## 📧 Support

For issues, questions, or contributions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the documentation in code comments

## 🎓 Assignment Context

This project was developed as part of an intelligent parsing and structuring system for USB PD specifications. The goal is to convert complex technical PDFs into structured, machine-readable formats suitable for:
- Documentation systems
- Knowledge bases
- LLM training data
- Automated analysis tools

## 🔄 Version History

- **v1.0.0** - Initial release with core parsing functionality
- ToC extraction with multi-regex support
- High-fidelity content extraction
- Validation and reporting system
- CLI interface

---

**Built with** ❤️ **for USB Power Delivery specification parsing**