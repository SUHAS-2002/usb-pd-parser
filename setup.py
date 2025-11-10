# setup.py
"""
Setup configuration for USB PD Parser.
"""
from setuptools import setup, find_packages
import os
from typing import List, Dict, Any


class PackageConfig:
    """Manages configuration for the usb-pd-parser package setup."""
    
    def __init__(self):
        self.name = "usb-pd-parser"
        self.version = "1.0.0"
        self.author = "Assignment Solution Team"
        self.author_email = "support@example.com"
        self.url = "https://github.com/yourusername/usb-pd-parser"
        self.python_requires = ">=3.8"

    def get_description(self) -> str:
        """Return the package description."""
        return "USB Power Delivery Specification Parser"

    def get_long_description(self) -> str:
        """Read the long description from README.md with error handling."""
        readme_path = "README.md"
        if os.path.exists(readme_path):
            with open(readme_path, "r", encoding="utf-8") as f:
                return f.read()
        return self.get_description()

    def get_requirements(self) -> List[str]:
        """Read requirements from requirements.txt, keeping lines short."""
        requirements_path = "requirements.txt"
        if not os.path.exists(requirements_path):
            return []
        with open(requirements_path, "r", encoding="utf-8") as f:
            return [
                line.strip()
                for line in f
                if line.strip() and not line.startswith("#")
            ]

    def get_classifiers(self) -> List[str]:
        """Return package classifiers for PyPI."""
        return [
            "Development Status :: 4 - Beta",
            "Intended Audience :: Developers",
            "Topic :: Software Development :: Libraries",
            "License :: OSI Approved :: MIT License",
            "Programming Language :: Python :: 3",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
        ]

    def get_entry_points(self) -> Dict[str, List[str]]:
        """Return entry points for console scripts."""
        return {
            "console_scripts": [
                "usb-pd-parser=usb_pd_parser:main",
            ]
        }

    def get_setup_kwargs(self) -> Dict[str, Any]:
        """Return keyword arguments for setup() function."""
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "author_email": self.author_email,
            "description": self.get_description(),
            "long_description": self.get_long_description(),
            "long_description_content_type": "text/markdown",
            "url": self.url,
            "packages": find_packages(),
            "classifiers": self.get_classifiers(),
            "python_requires": self.python_requires,
            "install_requires": self.get_requirements(),
            "entry_points": self.get_entry_points(),
        }


def main():
    """Configure and run package setup."""
    config = PackageConfig()
    setup(**config.get_setup_kwargs())


if __name__ == "__main__":
    main()