"""
CSV I/O handler with resume capability.
"""

import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Set

from .models import EbookFile


class CSVHandler:
    """Handles CSV I/O with resume capability."""

    def __init__(self, csv_path: Path, batch_size: int = 100, resume_mode: bool = False):
        """
        Initialize CSV handler.

        Args:
            csv_path: Path to CSV file
            batch_size: Number of files to write in each batch
            resume_mode: Whether to enable resume mode (read existing file)
        """
        self.csv_path = Path(csv_path)
        self.batch_size = batch_size
        self.resume_mode = resume_mode
        self._processed_files: Set[str] = set()
        self._buffer: List[EbookFile] = []
        self._header_written = False

        if resume_mode and self.csv_path.exists():
            # Load existing processed files
            self._processed_files = self.get_processed_files()

    def write_header(self) -> None:
        """Write CSV header if not already written."""
        if self._header_written:
            return

        # Check if file exists and has content
        if self.csv_path.exists() and self.csv_path.stat().st_size > 0:
            self._header_written = True
            return

        # Write header
        with open(self.csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["relative_path", "filename", "file_size", "full_path", "processed_at"],
            )
            writer.writeheader()

        self._header_written = True

    def write_batch(self, files: List[EbookFile]) -> None:
        """
        Write a batch of files to CSV.

        Args:
            files: List of EbookFile objects to write
        """
        if not files:
            return

        self.write_header()

        # Append to buffer
        self._buffer.extend(files)

        # Write if buffer is full
        if len(self._buffer) >= self.batch_size:
            self._flush_buffer()

    def _flush_buffer(self) -> None:
        """Flush buffer to CSV file."""
        if not self._buffer:
            return

        with open(self.csv_path, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["relative_path", "filename", "file_size", "full_path", "processed_at"],
            )

            for file in self._buffer:
                row = file.to_dict()
                row["processed_at"] = datetime.now(timezone.utc).isoformat()
                writer.writerow(row)

        self._buffer.clear()

    def flush(self) -> None:
        """Flush any remaining buffer to CSV file."""
        self._flush_buffer()

    def read_all(self, base_path: Path) -> List[EbookFile]:
        """
        Read all files from CSV.

        Args:
            base_path: Base path for resolving relative paths

        Returns:
            List of EbookFile objects
        """
        if not self.csv_path.exists():
            return []

        files = []
        with open(self.csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    file = EbookFile.from_dict(row, base_path)
                    files.append(file)
                except (KeyError, ValueError):
                    # Skip invalid rows
                    continue

        return files

    def get_processed_files(self) -> Set[str]:
        """
        Get set of full paths that have been processed (for resume).

        Returns:
            Set of full path strings
        """
        if not self.csv_path.exists():
            return set()

        processed = set()
        with open(self.csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if "full_path" in row:
                    processed.add(row["full_path"])

        return processed

    def get_last_processed_index(self) -> int:
        """
        Get the index of the last processed file (for resume).

        Returns:
            Number of rows in CSV (excluding header)
        """
        if not self.csv_path.exists():
            return 0

        count = 0
        with open(self.csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for _ in reader:
                count += 1

        return count
