"""
USB PD Content Validator
Validates USB Power Delivery content against a table of contents.
"""

import logging
from pathlib import Path
from .loader import DataLoader
from .matcher import SectionMatcher
from .reporter import ReportGenerator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TOCValidator:
    """Orchestrates loading, matching, and reporting for USB PD validation."""

    def __init__(
        self,
        similarity_threshold: float = 0.85,
        strict: bool = False
    ):
        """
        Initialize the validator with configuration.

        Args:
            similarity_threshold (float): Threshold for matching similarity (0.0-1.0).
            strict (bool): Enable strict validation mode.
        """
        self.threshold = similarity_threshold
        self.strict = strict
        self.loader = DataLoader()
        self.matcher = SectionMatcher(threshold=similarity_threshold)
        self.reporter = ReportGenerator()

    def validate(
        self,
        toc_path: str,
        chunks_path: str,
        output: str = "validation_report.json"
    ) -> dict:
        """
        Run the full validation pipeline.

        Args:
            toc_path (str): Path to the TOC file (JSONL format).
            chunks_path (str): Path to the content chunks file (JSONL format).
            output (str): Path to save the validation report.

        Returns:
            dict: Validation report containing results and quality score.

        Raises:
            ValueError: If TOC entries cannot be loaded.
        """
        logger.info("=" * 70)
        logger.info("Starting USB PD Validation v2.1")
        logger.info("=" * 70)

        toc_entries = self.loader.load_toc(toc_path)
        chunks = self.loader.load_chunks(chunks_path)

        if not toc_entries:
            raise ValueError("No TOC entries loaded")

        results = self.matcher.analyze(toc_entries, chunks)
        report = self.reporter.build_report(results, toc_entries, chunks)
        self.reporter.save_and_print(report, output)

        return report


def main() -> int:
    """
    Parse command-line arguments and run the validator.

    Returns:
        int: Exit code (0: success, 1: score >= 70, 2: score < 70, 3: error).
    """
    import argparse

    parser = argparse.ArgumentParser(description="USB PD Validator v2.1")
    parser.add_argument("toc_file", help="Path to toc.jsonl")
    parser.add_argument("chunks_file", help="Path to content.jsonl")
    parser.add_argument(
        "-o",
        "--output",
        default="validation_report.json",
        help="Output report path"
    )
    parser.add_argument(
        "-t",
        "--threshold",
        type=float,
        default=0.85,
        help="Similarity threshold (0.0-1.0)"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict validation mode"
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        validator = TOCValidator(args.threshold, args.strict)
        report = validator.validate(args.toc_file, args.chunks_file, args.output)
        score = report.quality_score
        return 0 if score >= 85 else 1 if score >= 70 else 2
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=args.verbose)
        return 3


if __name__ == "__main__":
    exit(main())