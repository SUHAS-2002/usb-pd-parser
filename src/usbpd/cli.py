import argparse
from pathlib import Path

from src.utils.logger_config import setup_logging
from src.usb_pd_parser import USBPDParser
from src.validator.toc_validator import TOCValidator
from src.validator.report_generator import ReportGenerator
from src.reports.excel_coverage_report import ExcelReportGenerator
from src.generators.spec_generator import SpecJSONLGenerator
from src.generators.metadata_generator import MetadataGenerator
from src.reports.excel_validation_report import ExcelValidationReport


# Private module-level constant
__DATA_DIR = Path("data")
__DATA_DIR.mkdir(exist_ok=True)


def _get_data_dir() -> Path:
    """Get data directory path (protected)."""
    return __DATA_DIR


# ------------------------------------------------------------------
# Utilities
# ------------------------------------------------------------------
def force_data_path(filename: str) -> str:
    """Ensure all output files stay inside /data directory."""
    return str(_get_data_dir() / Path(filename).name)


# ------------------------------------------------------------------
# Command Handlers (SRP-compliant)
# ------------------------------------------------------------------
def _handle_parse(args) -> None:
    runner = USBPDParser(args.pdf_path, args.out)
    runner.run()


def _handle_validate(args) -> None:
    """
    Validate TOC vs chunks and generate validation score report.
    """
    report_path = force_data_path(args.report)

    # 1) Run validation
    validator = TOCValidator()
    raw = validator.validate(args.toc, args.chunks, report_path)

    # 2) Generate validation score report (NEW API)
    generator = ReportGenerator(
        raw_validation=raw,
        output_path="data/score_report.jsonl",
    )
    generator.generate()


def _handle_excel(args) -> None:
    output = force_data_path(args.output)

    with ExcelReportGenerator(
        toc_path=args.toc,
        chunks_path=args.chunks,
        output_xlsx=output,
    ) as generator:
        generator.generate()

    print(f"Excel coverage report saved → {output}")


def _handle_export_spec(args) -> None:
    output = force_data_path(args.output)
    SpecJSONLGenerator().generate(args.toc, args.chunks, output)
    print(f"Unified spec JSONL saved → {output}")


def _handle_export_metadata(args) -> None:
    output = force_data_path(args.output)
    MetadataGenerator().generate(args.toc, args.chunks, output)
    print(f"Metadata JSONL saved → {output}")


def _handle_export_validation_xlsx(args) -> None:
    output = force_data_path(args.output)

    with ExcelValidationReport(args.report, output) as generator:
        generator.generate()

    print(f"Validation Excel saved → {output}")


# ------------------------------------------------------------------
# CLI Setup
# ------------------------------------------------------------------
def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="usbpd",
        description="USB Power Delivery Specification Parser CLI",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # PARSE
    p_parse = sub.add_parser("parse", help="Parse PDF → TOC + CONTENT JSONL")
    p_parse.add_argument("pdf_path", help="Path to the PDF file")
    p_parse.add_argument("--out", default="data", help="Output directory")

    # VALIDATE
    p_val = sub.add_parser("validate", help="Validate extracted content")
    p_val.add_argument("--toc", default="data/usb_pd_toc.jsonl")
    p_val.add_argument("--chunks", default="data/usb_pd_spec.jsonl")
    p_val.add_argument("--report", default="validation_report.jsonl")

    # EXCEL COVERAGE
    p_excel = sub.add_parser("excel", help="Generate Excel coverage report")
    p_excel.add_argument("--toc", required=True)
    p_excel.add_argument("--chunks", required=True)
    p_excel.add_argument("--output", default="coverage.xlsx")

    # EXPORT-SPEC
    p_spec = sub.add_parser("export-spec", help="Generate merged spec JSONL")
    p_spec.add_argument("--toc", required=True)
    p_spec.add_argument("--chunks", required=True)
    p_spec.add_argument("--output", default="usb_pd_spec.jsonl")

    # EXPORT-METADATA
    p_meta = sub.add_parser(
        "export-metadata", help="Generate metadata JSONL"
    )
    p_meta.add_argument("--toc", required=True)
    p_meta.add_argument("--chunks", required=True)
    p_meta.add_argument("--output", default="usb_pd_metadata.jsonl")

    # EXPORT VALIDATION XLSX
    p_val_xlsx = sub.add_parser(
        "export-validation-xlsx",
        help="Generate Excel file from validation_report.jsonl",
    )
    p_val_xlsx.add_argument("--report", required=True)
    p_val_xlsx.add_argument(
        "--output", default="validation_report.xlsx"
    )

    return parser


# ------------------------------------------------------------------
# Entry Point
# ------------------------------------------------------------------
def main() -> None:
    setup_logging(use_console=True)
    parser = _build_parser()
    args = parser.parse_args()

    handlers = {
        "parse": _handle_parse,
        "validate": _handle_validate,
        "excel": _handle_excel,
        "export-spec": _handle_export_spec,
        "export-metadata": _handle_export_metadata,
        "export-validation-xlsx": _handle_export_validation_xlsx,
    }

    handlers[args.command](args)


if __name__ == "__main__":
    main()
