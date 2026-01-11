"""
CLI command definitions for ebook-calibre-analyzer.
"""

import argparse
from datetime import datetime, timezone
from pathlib import Path


def get_default_output_path() -> Path:
    """Get default output CSV path in working directory."""
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return Path.cwd() / f"missing_from_calibre_{timestamp}.csv"


def get_default_file_extensions_str() -> str:
    """Get default file extensions as comma-separated string for help text."""
    from .utils import get_default_file_extensions

    exts = get_default_file_extensions()
    return ", ".join(ext.replace(".", "") for ext in exts)


def create_analyze_parser(subparsers) -> argparse.ArgumentParser:
    """Create parser for analyze command."""
    parser = subparsers.add_parser(
        "analyze",
        help="Analyze ebooks folder and compare against Calibre library",
        description="Analyze ebook files in datalake and compare against Calibre library",
    )

    parser.add_argument("ebooks_folder", type=Path, help="Path to ebooks datalake folder")

    parser.add_argument("calibre_library_folder", type=Path, help="Path to Calibre library folder")

    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Output CSV path (default: ./missing_from_calibre_YYYYMMDD_HHMMSS.csv in working directory)",
    )

    default_exts_str = get_default_file_extensions_str()
    parser.add_argument(
        "--file-types",
        nargs="+",
        default=None,
        help=f"File extensions to include (default: {default_exts_str})",
    )

    parser.add_argument("--resume", type=Path, default=None, help="Resume from existing CSV file")

    parser.add_argument(
        "--use-gpu", action="store_true", help="Enable GPU acceleration for hashing (requires CUDA)"
    )

    parser.add_argument("--gpu-device", type=int, default=0, help="GPU device ID (default: 0)")

    parser.add_argument(
        "--gpu-threshold",
        type=str,
        default="100MB",
        help="File size threshold for GPU processing (default: 100MB)",
    )

    parser.add_argument(
        "--batch-size", type=int, default=100, help="CSV write batch size (default: 100)"
    )

    parser.add_argument(
        "--workers", type=int, default=10, help="CPU worker processes (default: 10)"
    )

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    parser.add_argument("--progress", action="store_true", help="Show progress bars")

    return parser


def create_copy_parser(subparsers) -> argparse.ArgumentParser:
    """Create parser for copy command."""
    parser = subparsers.add_parser(
        "copy",
        help="Copy files from CSV to Calibre import folder",
        description="Copy files from CSV to Calibre import folder (flat structure)",
    )

    parser.add_argument("csv_file", type=Path, help="Path to CSV file with files to copy")

    parser.add_argument("ebooks_folder", type=Path, help="Path to ebooks datalake folder (source)")

    parser.add_argument("target_folder", type=Path, help="Path to Calibre import folder (target)")

    parser.add_argument(
        "--conflict-handling",
        choices=["rename", "skip", "overwrite"],
        default="rename",
        help="How to handle filename conflicts: rename, skip, overwrite (default: rename)",
    )

    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be copied without copying"
    )

    parser.add_argument("--workers", type=int, default=4, help="Parallel copy workers (default: 4)")

    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    parser.add_argument("--progress", action="store_true", help="Show progress bars")

    return parser


def create_parser() -> argparse.ArgumentParser:
    """Create main argument parser."""
    parser = argparse.ArgumentParser(
        prog="ebook-analyzer",
        description="Analyze ebook files in datalake and compare against Calibre library",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run", required=True)

    create_analyze_parser(subparsers)
    create_copy_parser(subparsers)

    return parser


def parse_size(size_str: str) -> int:
    """
    Parse size string to bytes.

    Supports: KB, MB, GB, TB (case-insensitive)
    """
    size_str = size_str.strip().upper()

    multipliers = {
        "KB": 1024,
        "MB": 1024**2,
        "GB": 1024**3,
        "TB": 1024**4,
    }

    for suffix, multiplier in multipliers.items():
        if size_str.endswith(suffix):
            number = float(size_str[: -len(suffix)])
            return int(number * multiplier)

    # Try to parse as plain number (assume bytes)
    try:
        return int(size_str)
    except ValueError as err:
        raise ValueError(f"Invalid size format: {size_str}") from err
