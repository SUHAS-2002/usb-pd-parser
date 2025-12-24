import argparse
from pathlib import Path

from src.usb_pd_parser import USBPDParser
from src.validator.toc_validator import TOCValidator
from src.validator.report_generator import ReportGenerator
from src.excel_report import ExcelReportGenerator
from src.generators.spec_generator import SpecJSONLGenerator
from src.generators.metadata_generator import MetadataGenerator
from src.excel_validation_report import ExcelValidationReport


class USBPDCLI:
    """
    Command-line interface controller for USB-PD parser.

    Encapsulation rules:
    - run() is the ONLY public method
    - command handling is private
    - filesystem rules are encapsulated
    """

    def __init__(self) -> None:
        self.__data_dir = Path("data")
        self.__data_dir.mkdir(exist_ok=True)

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def run(self) -> None:
        parser = self._build_parser()
        args = parser.parse_args()
        self._dispatch(args)

    # ---------------------------------------------------------
    # Parser construction (protected)
    # ---------------------------------------------------------
    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog="usbpd",
            description="USB Power Delivery Specification Parser CLI",
        )

        sub = parser.add_subparsers(
            dest="command",
            required=True,
        )

        self._add_parse_cmd(sub)
        self._add_validate_cmd(sub)
        self._add_excel_cmd(sub)
        self._add_export_spec_cmd(sub)
        self._add_export_metadata_cmd(sub)
        self._add_export_validation_xlsx_cmd(sub)

        return parser

    # ---------------------------------------------------------
    # Command registration helpers
    # ---------------------------------------------------------
    def _add_parse_cmd(self, sub) -> None:
        p = sub.add_parser(
            "parse",
            help="Parse PDF → TOC + CONTENT JSONL",
        )
        p.add_argument("pdf_path")
        p.add_argument("--out", default="data")

    def _add_validate_cmd(self, sub) -> None:
        p = sub.add_parser(
            "validate",
            help="Validate extracted content",
        )
        p.add_argument("--toc", default="data/usb_pd_toc.jsonl")
        p.add_argument("--chunks", default="data/usb_pd_spec.jsonl")
        p.add_argument("--report", default="validation_report.json")

    def _add_excel_cmd(self, sub) -> None:
        p = sub.add_parser(
            "excel",
            help="Generate Excel coverage report",
        )
        p.add_argument("--toc", required=True)
        p.add_argument("--chunks", required=True)
        p.add_argument("--output", default="coverage.xlsx")

    def _add_export_spec_cmd(self, sub) -> None:
        p = sub.add_parser(
            "export-spec",
            help="Generate merged spec JSONL",
        )
        p.add_argument("--toc", required=True)
        p.add_argument("--chunks", required=True)
        p.add_argument("--output", default="usb_pd_spec.jsonl")

    def _add_export_metadata_cmd(self, sub) -> None:
        p = sub.add_parser(
            "export-metadata",
            help="Generate metadata JSONL",
        )
        p.add_argument("--toc", required=True)
        p.add_argument("--chunks", required=True)
        p.add_argument("--output", default="usb_pd_metadata.jsonl")

    def _add_export_validation_xlsx_cmd(self, sub) -> None:
        p = sub.add_parser(
            "export-validation-xlsx",
            help="Generate Excel from validation report",
        )
        p.add_argument("--report", required=True)
        p.add_argument("--output", default="validation_report.xlsx")

    # ---------------------------------------------------------
    # Command dispatch (private)
    # ---------------------------------------------------------
    def _dispatch(self, args) -> None:
        cmd = args.command

        if cmd == "parse":
            self.__handle_parse(args)
        elif cmd == "validate":
            self.__handle_validate(args)
        elif cmd == "excel":
            self.__handle_excel(args)
        elif cmd == "export-spec":
            self.__handle_export_spec(args)
        elif cmd == "export-metadata":
            self.__handle_export_metadata(args)
        elif cmd == "export-validation-xlsx":
            self.__handle_export_validation_xlsx(args)

    # ---------------------------------------------------------
    # Command handlers (private)
    # ---------------------------------------------------------
    def __handle_parse(self, args) -> None:
        runner = USBPDParser(args.pdf_path, args.out)
        runner.run()

    def __handle_validate(self, args) -> None:
        report_path = self.__force_data_path(args.report)

        validator = TOCValidator()
        raw = validator.validate(
            args.toc,
            args.chunks,
            report_path,
        )

        reporter = ReportGenerator()
        rep = reporter.generate(raw)
        reporter.print_console(rep)
        reporter.save(rep)

    def __handle_excel(self, args) -> None:
        output = self.__force_data_path(args.output)

        generator = ExcelReportGenerator(
            toc_path=args.toc,
            chunks_path=args.chunks,
            output_xlsx=output,
        )
        generator.generate()

        print(f"Excel coverage report saved → {output}")

    def __handle_export_spec(self, args) -> None:
        output = self.__force_data_path(args.output)

        SpecJSONLGenerator().generate(
            args.toc,
            args.chunks,
            output,
        )

        print(f"Unified spec JSONL saved → {output}")

    def __handle_export_metadata(self, args) -> None:
        output = self.__force_data_path(args.output)

        MetadataGenerator().generate(
            args.toc,
            args.chunks,
            output,
        )

        print(f"Metadata JSONL saved → {output}")

    def __handle_export_validation_xlsx(self, args) -> None:
        output = self.__force_data_path(args.output)

        ExcelValidationReport().generate(
            args.report,
            output,
        )

        print(f"Validation Excel saved → {output}")

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------
    def __force_data_path(self, filename: str) -> str:
        return str(self.__data_dir / Path(filename).name)


# -------------------------------------------------------------
# Entry point
# -------------------------------------------------------------
def main() -> None:
    USBPDCLI().run()


if __name__ == "__main__":
    main()
