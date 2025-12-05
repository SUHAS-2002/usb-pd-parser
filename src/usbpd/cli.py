import argparse
from src.usb_pd_parser import USBPDParser
from src.validator.toc_validator import TOCValidator
from src.validator.report_generator import ReportGenerator
from src.excel_report import ExcelReportGenerator


def main():
    parser = argparse.ArgumentParser(
        prog="usbpd",
        description="USB Power Delivery Specification Parser CLI"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # ---------------------------------------------------------
    # PARSE COMMAND
    # ---------------------------------------------------------
    p_parse = sub.add_parser("parse", help="Parse PDF → TOC + Chunks")
    p_parse.add_argument("pdf_path", help="Path to PDF file")
    p_parse.add_argument("--out", default="data", help="Output directory")

    # ---------------------------------------------------------
    # VALIDATE COMMAND
    # ---------------------------------------------------------
    p_val = sub.add_parser("validate", help="Validate results")
    p_val.add_argument("--toc", default="data/usb_pd_toc.jsonl")
    p_val.add_argument("--chunks", default="data/usb_pd_content.jsonl")
    p_val.add_argument("--report", default="validation_report.json")

    # ---------------------------------------------------------
    # EXPORT-XLSX COMMAND
    # ---------------------------------------------------------
    p_xlsx = sub.add_parser("export-xlsx", help="Export validation results to Excel")
    p_xlsx.add_argument("--toc", required=True, help="Path to TOC JSONL file")
    p_xlsx.add_argument("--chunks", required=True, help="Path to content JSONL file")
    p_xlsx.add_argument("--output", default="validation_report.xlsx", help="Output Excel filename")

    args = parser.parse_args()

    # ---------------------------------------------------------
    # HANDLE parse
    # ---------------------------------------------------------
    if args.command == "parse":
        runner = USBPDParser(args.pdf_path, args.out)
        runner.run()

    # ---------------------------------------------------------
    # HANDLE validate
    # ---------------------------------------------------------
    elif args.command == "validate":
        validator = TOCValidator()
        raw = validator.validate(args.toc, args.chunks, args.report)

        rep = ReportGenerator().generate(raw)
        ReportGenerator().print_console(rep)
        ReportGenerator().save(rep)

    # ---------------------------------------------------------
    # HANDLE export-xlsx
    # ---------------------------------------------------------
    elif args.command == "export-xlsx":
        generator = ExcelReportGenerator(
            toc_path=args.toc,
            chunks_path=args.chunks,
            output_xlsx=args.output
        )
        generator.generate()
        print(f"Excel report saved to: {args.output}")
