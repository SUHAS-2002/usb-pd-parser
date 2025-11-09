"""
USB PD Content Validator 
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
    """Main validator orchestrating loading, matching, and reporting."""

    def __init__(self, similarity_threshold: float = 0.85, strict: bool = False):
        self.threshold = similarity_threshold
        self.strict = strict
        self.loader = DataLoader()
        self.matcher = SectionMatcher(threshold=similarity_threshold)
        self.reporter = ReportGenerator()

    def validate(
        self,
        toc_path: str,
        chunks_path: str,
        output: str = "validation_report.json",
    ):
        """Run full validation pipeline."""
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
    import argparse

    parser = argparse.ArgumentParser(description="USB PD Validator v2.1")
    parser.add_argument("toc_file", help="Path to toc.jsonl")
    parser.add_argument("chunks_file", help="Path to content.jsonl")
    parser.add_argument("-o", "--output", default="validation_report.json")
    parser.add_argument("-t", "--threshold", type=float, default=0.85)
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        validator = TOCValidator(args.threshold, args.strict)
        report = validator.validate(
            args.toc_file, args.chunks_file, args.output
        )
        score = report.quality_score
        return 0 if score >= 85 else 1 if score >= 70 else 2
    except Exception as e:
        logger.error(f"Validation failed: {e}", exc_info=args.verbose)
        return 3


if __name__ == "__main__":
    exit(main())