"""
Extract ALL pages from a PDF using HighFidelityExtractor.

DEBUG ONLY:
- Extracts raw pages
- Writes JSONL output
- Does NOT extract TOC or sections
"""

import json
from pathlib import Path

from src.extractors.high_fidelity_extractor import (
    HighFidelityExtractor,
)


class PageExtractionDebugger:
    """
    Debug utility for inspecting raw page extraction.

    Encapsulation rules:
    - extract() is the ONLY public method
    - file I/O and logging are private
    """

    # ---------------------------------------------------------
    # Public API
    # ---------------------------------------------------------
    def extract(
        self,
        pdf_path: str,
        output: str = "data/all_pages.jsonl",
    ) -> Path:
        self.__pdf_path = Path(pdf_path)
        self.__output_path = Path(output)

        pages = self.__extract_pages()
        self.__persist(pages)

        print(f"Saved → {self.__output_path}")
        return self.__output_path

    # ---------------------------------------------------------
    # Private helpers
    # ---------------------------------------------------------
    def __extract_pages(self):
        extractor = HighFidelityExtractor()

        print(f"Extracting pages from: {self.__pdf_path}")
        pages = extractor.extract(str(self.__pdf_path))

        if not pages:
            raise RuntimeError("No pages extracted.")

        print(f"Extracted {len(pages)} pages.")
        return pages

    # ---------------------------------------------------------
    def __persist(self, pages) -> None:
        self.__output_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with self.__output_path.open(
            "w", encoding="utf-8"
        ) as f:
            for obj in pages:
                f.write(
                    json.dumps(
                        obj,
                        ensure_ascii=False,
                    )
                    + "\n"
                )


# -------------------------------------------------------------
# Debug entry point
# -------------------------------------------------------------
def main() -> None:
    pdf = "data/usb_pd_parser.pdf"
    PageExtractionDebugger().extract(pdf)


if __name__ == "__main__":
    main()
