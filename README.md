# USB PD Parser - Quick Start Guide  
A complete, high-fidelity parsing pipeline for the  
**USB Power Delivery Specification (USB-IF)**  
Built with clean OOP architecture and full CLI support.

---

# 📦 Project Structure (Updated for New Architecture)

usb-pd-parser/
├── data/
│   ├── usb_pd_toc.jsonl
│   ├── usb_pd_content.jsonl
│   ├── usb_pd_spec.jsonl
│   ├── usb_pd_metadata.jsonl
│   ├── validation_report.json
│   └── validation_report.xlsx
│
├── src/
│   ├── extractors/
│   │   ├── high_fidelity_extractor.py       ✓ Block text + OCR extractor
│   │   ├── toc_extractor.py                 ✓ Multi-regex TOC extraction
│   │   └── section_builder.py               ✓ TOC-aware content slicing
│   │
│   ├── validator/
│   │   ├── toc_validator.py                 ✓ Validates TOC vs content
│   │   ├── matcher.py                       ✓ Title/page matching engine
│   │   └── report_generator.py              ✓ Scoring + recommendations
│   │
│   ├── generators/
│   │   ├── spec_jsonl_generator.py          ✓ Builds final spec JSONL
│   │   └── metadata_generator.py            ✓ Document statistics
│   │
│   ├── usbpd/
│   │   ├── cli.py                           ✓ Main CLI interface
│   │   └── __init__.py
│   │
│   ├── schemas/
│   │   ├── toc_schema.json                  ✓ JSON schema for TOC
│   │   └── content_schema.json              ✓ JSON schema for sections
│   │
│   └── usb_pd_parser.py                     ✓ End-to-end orchestrator
│
├── requirements.txt                         ✓ Dependencies
└── README.md                                ✓ Documentation


mkdir usb-pd-parser
cd usb-pd-parser

python -m venv venv
venv\Scripts\activate

python -m pip install --upgrade pip
pip install -r requirements.txt


