"""
Centralized logging configuration for USB PD Parser.

Provides:
- Dedicated log file (e.g. logs/usbpd_parser.log)
- Input/output metadata and object sizes for key functions
- Execution time and memory usage for major steps
- Exception and error logging

Used to improve reliability and traceability during development and interviews.
"""

from __future__ import annotations

import logging
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional
from functools import wraps


# Default log directory relative to project root
__LOG_DIR_NAME = "logs"
__LOG_FILE_NAME = "usbpd_parser.log"


def get_log_dir(project_root: Optional[Path] = None) -> Path:
    """Return logs directory; create if missing."""
    if project_root is None:
        project_root = Path(__file__).resolve().parent.parent.parent
    log_dir = project_root / __LOG_DIR_NAME
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def get_log_path(project_root: Optional[Path] = None) -> Path:
    """Return full path to the main log file."""
    return get_log_dir(project_root) / __LOG_FILE_NAME


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    use_console: bool = True,
) -> None:
    """
    Configure root logger with file and optional console handler.

    Parameters
    ----------
    level : int
        Logging level (default: logging.INFO)
    log_file : Path, optional
        If set, logs are appended to this file
    use_console : bool
        If True, also log to stderr
    """
    root = logging.getLogger()
    root.setLevel(level)

    fmt = (
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    formatter = logging.Formatter(fmt, datefmt="%Y-%m-%d %H:%M:%S")

    if log_file is None:
        log_file = get_log_path()
    log_file = Path(log_file)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(level)
    fh.setFormatter(formatter)
    root.addHandler(fh)

    if use_console:
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(level)
        ch.setFormatter(formatter)
        root.addHandler(ch)


def log_io_and_time(
    logger: Optional[logging.Logger] = None,
    log_input_size: bool = True,
    log_output_size: bool = True,
):
    """
    Decorator to log function inputs/outputs and execution time.

    Logs:
    - Function name and (optionally) input size/length
    - Execution time in seconds
    - (Optionally) output size/length

    Use on key pipeline functions for interview/demo clarity.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            name = func.__name__
            log = logger or logging.getLogger(func.__module__)

            def _size(obj: Any) -> str:
                if obj is None:
                    return "0"
                if hasattr(obj, "__len__"):
                    return str(len(obj))
                return "N/A"

            if log_input_size and args:
                first = args[0]
                log.info(
                    "ENTER %s | input_size=%s",
                    name,
                    _size(first),
                )
            else:
                log.info("ENTER %s", name)

            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                if log_output_size and result is not None:
                    log.info(
                        "EXIT %s | time_sec=%.3f | output_size=%s",
                        name,
                        elapsed,
                        _size(result),
                    )
                else:
                    log.info(
                        "EXIT %s | time_sec=%.3f",
                        name,
                        elapsed,
                    )
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                log.exception(
                    "EXCEPTION in %s after %.3fs: %s",
                    name,
                    elapsed,
                    e,
                )
                raise

        return wrapper

    return decorator


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module name."""
    return logging.getLogger(name)
