import argparse
from pathlib import Path

from src.usb_pd_parser import USBPDParser
from src.validator.toc_validator import TOCValidator
from src.validator.report_generator import ReportGenerator
from src.excel_report import ExcelReportGenerator
from src.generators.spec_generator import SpecJSONLGenerator
from src.generators.metadata_generator import MetadataGenerator
from src.excel_validation_report import ExcelValidationReport  # NEW


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def force_data_path(filename: str) -> str:
    """Ensure all output files stay inside /data directory."""
    return str(DATA_DIR / Path(filename).name)


def main():
    parser = argparse.ArgumentParser(
        prog="usbpd",
        description="USB Power Delivery Specification Parser CLI"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # ---------------------------------------------------------
    # PARSE COMMAND
    # ---------------------------------------------------------
    p_parse = sub.add_parser("parse", help="Parse PDF → TOC + CONTENT JSONL")
    p_parse.add_argument("pdf_path", help="Path to the PDF file")
    p_parse.add_argument("--out", default="data", help="Output directory")

    # ---------------------------------------------------------
    # VALIDATE COMMAND
    # ---------------------------------------------------------
    p_val = sub.add_parser("validate", help="Validate extracted content")
    p_val.add_argument("--toc", default="data/usb_pd_toc.jsonl")
    p_val.add_argument("--chunks", default="data/usb_pd_spec.jsonl")
    p_val.add_argument("--report", default="validation_report.json")

    # ---------------------------------------------------------
    # EXCEL COVERAGE REPORT
    # ---------------------------------------------------------
    p_excel = sub.add_parser("excel", help="Generate Excel coverage report")
    p_excel.add_argument("--toc", required=True)
    p_excel.add_argument("--chunks", required=True)
    p_excel.add_argument("--output", default="coverage.xlsx")

    # ---------------------------------------------------------
    # EXPORT-SPEC (merged spec JSONL)
    # ---------------------------------------------------------
    p_spec = sub.add_parser("export-spec", help="Generate merged spec JSONL")
    p_spec.add_argument("--toc", required=True)
    p_spec.add_argument("--chunks", required=True)
    p_spec.add_argument("--output", default="usb_pd_spec.jsonl")

    # ---------------------------------------------------------
    # EXPORT-METADATA
    # ---------------------------------------------------------
    p_meta = sub.add_parser("export-metadata", help="Generate metadata JSONL")
    p_meta.add_argument("--toc", required=True)
    p_meta.add_argument("--chunks", required=True)
    p_meta.add_argument("--output", default="usb_pd_metadata.jsonl")

    # ---------------------------------------------------------
    # NEW: EXPORT VALIDATION XLSX
    # ---------------------------------------------------------
    p_val_xlsx = sub.add_parser(
        "export-validation-xlsx",
        help="Generate Excel file from validation_report.json"
    )
    p_val_xlsx.add_argument("--report", required=True)
    p_val_xlsx.add_argument("--output", default="validation_report.xlsx")

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
        report_path = force_data_path(args.report)
        validator = TOCValidator()
        raw = validator.validate(args.toc, args.chunks, report_path)

        rep = ReportGenerator().generate(raw)
        ReportGenerator().print_console(rep)
        ReportGenerator().save(rep)

    # ---------------------------------------------------------
    # HANDLE excel coverage report
    # ---------------------------------------------------------
    elif args.command == "excel":
        output = force_data_path(args.output)
        generator = ExcelReportGenerator(
            toc_path=args.toc,
            chunks_path=args.chunks,
            output_xlsx=output
        )
        generator.generate()
        print(f"Excel coverage report saved → {output}")

    # ---------------------------------------------------------
    # HANDLE export-spec
    # ---------------------------------------------------------
    elif args.command == "export-spec":
        output = force_data_path(args.output)
        SpecJSONLGenerator().generate(args.toc, args.chunks, output)
        print(f"Unified spec JSONL saved → {output}")

    # ---------------------------------------------------------
    # HANDLE export-metadata
    # ---------------------------------------------------------
    elif args.command == "export-metadata":
        output = force_data_path(args.output)
        MetadataGenerator().generate(args.toc, args.chunks, output)
        print(f"Metadata JSONL saved → {output}")

    # ---------------------------------------------------------
    # HANDLE export-validation-xlsx  (FIXED)
    # ---------------------------------------------------------
    elif args.command == "export-validation-xlsx":
        output = force_data_path(args.output)
        generator = ExcelValidationReport()                 # FIXED
        generator.generate(args.report, output)             # FIXED
        print(f"Validation Excel saved → {output}")


if __name__ == "__main__":
    main()
