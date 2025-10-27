USB PD Parser - Quick Start Guide
📦 Complete File List
Create these files in your project directory:
usb-pd-parser/
├── usb_pd_parser.py ✓ Main parser
├── advanced_parser.py ✓ Advanced chunking
├── validator.py ✓ Validation module
├── requirements.txt ✓ Dependencies
├── setup.py ✓ Package setup
├── README.md ✓ Documentation
├── QUICK_START.md ✓ This file
├── .gitignore ✓ Git ignore
├── setup_and_run.sh ✓ Linux/Mac setup
├── setup_and_run.bat ✓ Windows setup
├── tests/
│ ├── **init**.py ✓ Test package
│ ├── test_parser.py ✓ Unit tests
│ └── sample_toc.txt ✓ Sample data
├── examples/
│ └── sample_output.jsonl ✓ Example output
└── data/
└── .gitkeep ✓ Placeholder

🚀 Installation Commands
Windows Commands
cmdREM Step 1: Create project directory
mkdir usb-pd-parser
cd usb-pd-parser

REM Step 2: Create all files (copy from artifacts above)
REM Save each file with its correct name

REM Step 3: Create virtual environment
python -m venv venv

REM Step 4: Activate virtual environment
venv\Scripts\activate

REM Step 5: Upgrade pip
python -m pip install --upgrade pip

REM Step 6: Install dependencies
pip install -r requirements.txt

REM Step 7: Verify installation
python usb_pd_parser.py --help
Linux/Mac Commands
bash# Step 1: Create project directory
mkdir usb-pd-parser
cd usb-pd-parser

# Step 2: Create all files (copy from artifacts above)

# Save each file with its correct name

# Step 3: Create virtual environment

python3 -m venv venv

# Step 4: Activate virtual environment

source venv/bin/activate

# Step 5: Upgrade pip

pip install --upgrade pip

# Step 6: Install dependencies

pip install -r requirements.txt

# Step 7: Make scripts executable

chmod +x setup_and_run.sh

# Step 8: Verify installation

python usb_pd_parser.py --help

📖 Usage Examples

1. Basic ToC Extraction
   bash# Parse PDF and extract ToC
   python usb_pd_parser.py data/usb_pd_spec.pdf

# Output: usb_pd_spec.jsonl

2. Custom Output File
   bashpython usb_pd_parser.py data/usb_pd_spec.pdf -o my_output.jsonl
3. With Custom Title
   bashpython usb_pd_parser.py data/usb_pd_spec.pdf \
    -t "USB Power Delivery Specification Rev 3.1" \
    -o usb_pd_rev31.jsonl
4. Verbose Mode (Debug)
   bashpython usb_pd_parser.py data/usb_pd_spec.pdf -v
5. Scan More Pages for ToC
   bashpython usb_pd_parser.py data/usb_pd_spec.pdf --pages 25
6. Advanced Parsing with Chunking
   python# Run in Python
   from advanced_parser import AdvancedUSBPDParser

parser = AdvancedUSBPDParser("data/usb_pd_spec.pdf")
chunks = parser.run(output_path="chunks.jsonl", start_page=10)

print(f"Created {len(chunks)} chunks") 7. Validate ToC Against Chunks
bashpython validator.py usb_pd_spec.jsonl chunks.jsonl -o validation_report.json 8. Run All Tests
bash# Run tests with coverage
pytest tests/ -v --cov=usb_pd_parser --cov-report=html

# View coverage report

# Open htmlcov/index.html in browser

🔧 Complete Workflow
Step-by-Step Process
bash# 1. Setup environment (one-time)
python3 -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Place your PDF

cp /path/to/your/usb_pd_spec.pdf data/

# 3. Extract Table of Contents

python usb_pd_parser.py data/usb_pd_spec.pdf -o usb_pd_toc.jsonl -v

# 4. (Optional) Advanced chunking

python -c "
from advanced_parser import AdvancedUSBPDParser
parser = AdvancedUSBPDParser('data/usb_pd_spec.pdf')
parser.run('chunks.jsonl', start_page=10)
"

# 5. (Optional) Validate results

python validator.py usb_pd_toc.jsonl chunks.jsonl

# 6. View results

cat usb_pd_toc.jsonl | head -5
cat validation_report.json

# 7. Run tests

pytest tests/ -v

📊 Expected Output Format
ToC JSONL Output (usb_pd_spec.jsonl)
json{"doc_title": "USB Power Delivery Specification Rev X", "section_id": "2", "title": "Overview", "full_path": "2 Overview", "page": 53, "level": 1, "parent_id": null, "tags": []}
{"doc_title": "USB Power Delivery Specification Rev X", "section_id": "2.1", "title": "Introduction", "full_path": "2.1 Introduction", "page": 53, "level": 2, "parent_id": "2", "tags": []}
{"doc_title": "USB Power Delivery Specification Rev X", "section_id": "2.1.2", "title": "Power Delivery Contract Negotiation", "full_path": "2.1.2 Power Delivery Contract Negotiation", "page": 53, "level": 3, "parent_id": "2.1", "tags": ["contract", "power"]}
Chunks JSONL Output (chunks.jsonl)
json{"section_path": "2.1.2 Power Delivery Contract Negotiation", "start_heading": "2.1.2 Power Delivery Contract Negotiation", "content": "...", "tables": ["Table 2-1"], "figures": ["Figure 2-3"], "page_range": [53, 55], "section_id": "2.1.2", "level": 3}
Validation Report (validation_report.json)
json{
"summary": "Parsed 92 of 94 ToC sections (97.9% match)",
"metrics": {
"toc_sections": 94,
"parsed_sections": 92,
"matched_sections": 92,
"missing_sections": 2,
"extra_sections": 0
},
"missing_sections": ["4.3.4 Advanced Feature", "5.2.1 Test Case"],
"recommendations": ["Review pages 73-75 for OCR quality"]
}

🧪 Testing Commands
bash# Run all tests
pytest tests/ -v

# Run specific test

pytest tests/test_parser.py::test_calculate_level -v

# Run with coverage

pytest tests/ --cov=usb_pd_parser --cov-report=term-missing

# Generate HTML coverage report

pytest tests/ --cov=usb_pd_parser --cov-report=html
open htmlcov/index.html

# Run with specific Python version

python3.9 -m pytest tests/ -v

🐛 Troubleshooting
Problem: No ToC entries found
bash# Solution 1: Increase page scan range
python usb_pd_parser.py data/spec.pdf --pages 30 -v

# Solution 2: Check PDF is text-based (not scanned image)

pdftotext data/spec.pdf - | head -20

# Solution 3: Try alternative PDF library

python -c "
import PyMuPDF
doc = PyMuPDF.open('data/spec.pdf')
print(doc[0].get_text())
"
Problem: Import errors
bash# Solution: Reinstall dependencies
pip install --upgrade --force-reinstall -r requirements.txt

# Or install individually

pip install pdfplumber==0.10.3
pip install PyMuPDF==1.23.8
Problem: Permission denied on Windows
cmdREM Run as administrator or use:
python -m pip install --user -r requirements.txt
Problem: Virtual environment not activating
bash# Linux/Mac
python3 -m venv --clear venv
source venv/bin/activate

# Windows

python -m venv --clear venv
venv\Scripts\activate.bat

📈 Performance Tips
For Large PDFs (>500 pages)
python# Use page range limits
from usb_pd_parser import USBPDParser

parser = USBPDParser("large_spec.pdf")

# Only scan first 20 pages for ToC

parser.run(output_path="output.jsonl", max_toc_pages=20)
For Multiple PDFs
bash# Batch process
for pdf in data/\*.pdf; do
echo "Processing $pdf..."
    python usb_pd_parser.py "$pdf" -o "${pdf%.pdf}.jsonl"
done
Memory Optimization
python# Process in chunks
from advanced_parser import AdvancedUSBPDParser

parser = AdvancedUSBPDParser("spec.pdf")

# Start from page 50 to skip front matter

parser.run(start_page=50)

🎯 Common Use Cases
Use Case 1: Extract ToC Only
bashpython usb_pd_parser.py data/spec.pdf -o toc.jsonl
Use Case 2: Full Document Analysis
bash# Step 1: Extract ToC
python usb_pd_parser.py data/spec.pdf -o toc.jsonl

# Step 2: Extract chunks

python -c "
from advanced_parser import AdvancedUSBPDParser
p = AdvancedUSBPDParser('data/spec.pdf')
p.run('chunks.jsonl')
"

# Step 3: Validate

python validator.py toc.jsonl chunks.jsonl
Use Case 3: Custom Tag Generation
python# Modify usb_pd_parser.py
def generate_tags(self, title: str) -> List[str]:
custom_keywords = {
'testing': ['test', 'validation', 'compliance'],
'electrical': ['voltage', 'current', 'resistance'], # Add your keywords
} # ... rest of implementation
Use Case 4: Export to Different Formats
pythonimport json
import csv

# Convert JSONL to CSV

with open('usb_pd_spec.jsonl', 'r') as f_in, \
 open('usb_pd_spec.csv', 'w', newline='') as f_out:

    first_line = json.loads(f_in.readline())
    writer = csv.DictWriter(f_out, fieldnames=first_line.keys())
    writer.writeheader()
    writer.writerow(first_line)

    for line in f_in:
        writer.writerow(json.loads(line))

📚 Python API Examples
Example 1: Programmatic Usage
pythonfrom usb_pd_parser import USBPDParser

# Initialize

parser = USBPDParser(
pdf_path="data/usb_pd_spec.pdf",
doc_title="USB PD Rev 3.1"
)

# Run parsing

parser.run(output_path="output.jsonl", max_toc_pages=15)

# Access results

for entry in parser.toc_entries:
print(f"{entry.section_id}: {entry.title} (Page {entry.page})")

# Get statistics

stats = parser.generate_statistics()
print(f"Total sections: {stats['total_entries']}")
print(f"By level: {stats['by_level']}")
Example 2: Custom Processing
pythonfrom usb_pd_parser import USBPDParser, TOCEntry

class CustomParser(USBPDParser):
def generate_tags(self, title: str): # Custom tag logic
tags = super().generate_tags(title)

        # Add custom tags
        if 'test' in title.lower():
            tags.append('testing')

        return tags

# Use custom parser

parser = CustomParser("data/spec.pdf")
parser.run()
Example 3: Filter and Export
pythonimport json
from usb_pd_parser import USBPDParser

parser = USBPDParser("data/spec.pdf")
parser.run()

# Filter level 2 sections only

level2_sections = [
entry.to_dict()
for entry in parser.toc_entries
if entry.level == 2
]

# Save filtered results

with open('level2_only.jsonl', 'w') as f:
for section in level2_sections:
f.write(json.dumps(section) + '\n')

🔍 Debugging Commands
bash# Enable debug logging
python usb_pd_parser.py data/spec.pdf -v 2>&1 | tee debug.log

# Check PDF structure

python -c "
import pdfplumber
with pdfplumber.open('data/spec.pdf') as pdf:
print(f'Pages: {len(pdf.pages)}')
print(f'First page text (100 chars): {pdf.pages[0].extract_text()[:100]}')
"

# Test regex patterns

python -c "
import re
from usb_pd_parser import USBPDParser
parser = USBPDParser.**new**(USBPDParser)
parser.TOC_PATTERNS = USBPDParser.TOC_PATTERNS
test_line = '2.1.2 Power Delivery Contract Negotiation ........... 53'
result = parser.parse_toc_line(test_line)
print(result)
"

# Validate JSONL output

python -c "
import json
with open('usb_pd_spec.jsonl', 'r') as f:
for i, line in enumerate(f, 1):
try:
json.loads(line)
except Exception as e:
print(f'Error on line {i}: {e}')
"

📝 Notes

Virtual environment activation is required before running commands
PDF must be text-based (not scanned images) for best results
Adjust --pages parameter based on your PDF's ToC length
Use -v flag for debugging and troubleshooting
Keep PDF files in data/ directory (they're gitignored)

🎓 Assignment Submission Checklist

usb_pd_parser.py - Main script
usb_pd_spec.jsonl - Output file
requirements.txt - Dependencies
README.md or code comments - Documentation
tests/ - Unit tests (optional but recommended)
Run successful on sample PDF
Output validated and correct

Quick Reference Card
bash# Setup
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Parse

python usb_pd_parser.py data/spec.pdf

# Test

pytest tests/ -v

# Validate

python validator.py toc.jsonl chunks.jsonl
