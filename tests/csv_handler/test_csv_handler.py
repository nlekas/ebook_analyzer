"""
Tests for CSVHandler class.
"""

import csv
from pathlib import Path

from ebook_calibre_analyzer.csv_handler import CSVHandler
from ebook_calibre_analyzer.models import EbookFile


class TestCSVHandler:
    """Test cases for CSVHandler class."""

    def test_init_sets_csv_path(self, temp_dir):
        """Test that __init__ initializes with provided csv_path."""
        csv_path = temp_dir / "test.csv"
        handler = CSVHandler(csv_path)
        assert handler.csv_path == csv_path

    def test_init_sets_batch_size(self, temp_dir):
        """Test that __init__ sets batch_size correctly."""
        csv_path = temp_dir / "test.csv"
        handler = CSVHandler(csv_path, batch_size=50)
        assert handler.batch_size == 50

    def test_init_loads_processed_files_in_resume_mode(self, temp_dir):
        """Test that __init__ loads processed_files when resume_mode=True and file exists."""
        csv_path = temp_dir / "test.csv"
        handler = CSVHandler(csv_path, resume_mode=False)

        # Write some files
        file1 = EbookFile(
            full_path=temp_dir / "file1.pdf",
            relative_path=Path("file1.pdf"),
            filename="file1.pdf",
            file_size=100,
            file_extension=".pdf",
        )
        handler.write_batch([file1])
        handler.flush()

        # Create new handler in resume mode
        handler2 = CSVHandler(csv_path, resume_mode=True)
        assert str(file1.full_path) in handler2._processed_files

    def test_write_header_writes_to_new_file(self, temp_dir):
        """Test that write_header writes header to new file."""
        csv_path = temp_dir / "test.csv"
        handler = CSVHandler(csv_path)
        handler.write_header()

        assert csv_path.exists()
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == [
                "relative_path",
                "filename",
                "file_size",
                "full_path",
                "processed_at",
            ]

    def test_write_header_does_not_overwrite_existing(self, temp_dir):
        """Test that write_header does not overwrite existing header."""
        csv_path = temp_dir / "test.csv"
        handler = CSVHandler(csv_path)
        handler.write_header()

        # Get original size
        original_size = csv_path.stat().st_size

        # Write header again
        handler.write_header()
        assert csv_path.stat().st_size == original_size

    def test_write_batch_adds_to_buffer(self, temp_dir):
        """Test that write_batch adds files to buffer."""
        csv_path = temp_dir / "test.csv"
        handler = CSVHandler(csv_path, batch_size=10)

        file1 = EbookFile(
            full_path=temp_dir / "file1.pdf",
            relative_path=Path("file1.pdf"),
            filename="file1.pdf",
            file_size=100,
            file_extension=".pdf",
        )
        handler.write_batch([file1])
        assert len(handler._buffer) == 1
        assert file1 in handler._buffer

    def test_write_batch_flushes_when_batch_size_reached(self, temp_dir):
        """Test that write_batch flushes buffer when batch_size reached."""
        csv_path = temp_dir / "test.csv"
        handler = CSVHandler(csv_path, batch_size=2)

        files = [
            EbookFile(
                full_path=temp_dir / f"file{i}.pdf",
                relative_path=Path(f"file{i}.pdf"),
                filename=f"file{i}.pdf",
                file_size=100,
                file_extension=".pdf",
            )
            for i in range(3)
        ]

        handler.write_batch(files)
        # The implementation adds all files to buffer, then flushes if buffer >= batch_size
        # With 3 files and batch_size=2: buffer becomes [0,1,2], then flushes all 3 (since 3 >= 2)
        # So buffer should be empty after flushing
        assert len(handler._buffer) == 0

    def test_flush_writes_remaining_buffer(self, temp_dir):
        """Test that flush flushes remaining buffer."""
        csv_path = temp_dir / "test.csv"
        handler = CSVHandler(csv_path, batch_size=10)

        file1 = EbookFile(
            full_path=temp_dir / "file1.pdf",
            relative_path=Path("file1.pdf"),
            filename="file1.pdf",
            file_size=100,
            file_extension=".pdf",
        )
        handler.write_batch([file1])
        assert len(handler._buffer) == 1

        handler.flush()
        assert len(handler._buffer) == 0

        # Verify file was written
        with open(csv_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]["filename"] == "file1.pdf"

    def test_read_all_returns_empty_for_nonexistent_file(self, temp_dir):
        """Test that read_all returns empty list for non-existent file."""
        csv_path = temp_dir / "nonexistent.csv"
        handler = CSVHandler(csv_path)
        assert handler.read_all(temp_dir) == []

    def test_read_all_reads_all_rows(self, temp_dir):
        """Test that read_all reads all rows from CSV."""
        csv_path = temp_dir / "test.csv"
        handler = CSVHandler(csv_path)

        files = [
            EbookFile(
                full_path=temp_dir / f"file{i}.pdf",
                relative_path=Path(f"file{i}.pdf"),
                filename=f"file{i}.pdf",
                file_size=100 + i,
                file_extension=".pdf",
            )
            for i in range(3)
        ]

        handler.write_batch(files)
        handler.flush()

        # Read back
        read_files = handler.read_all(temp_dir)
        assert len(read_files) == 3
        assert all(f.filename.startswith("file") for f in read_files)

    def test_get_processed_files_returns_empty_for_nonexistent(self, temp_dir):
        """Test that get_processed_files returns empty set for non-existent file."""
        csv_path = temp_dir / "nonexistent.csv"
        handler = CSVHandler(csv_path)
        assert handler.get_processed_files() == set()

    def test_get_processed_files_returns_all_full_paths(self, temp_dir):
        """Test that get_processed_files returns set of all full_path values."""
        csv_path = temp_dir / "test.csv"
        handler = CSVHandler(csv_path)

        files = [
            EbookFile(
                full_path=temp_dir / f"file{i}.pdf",
                relative_path=Path(f"file{i}.pdf"),
                filename=f"file{i}.pdf",
                file_size=100,
                file_extension=".pdf",
            )
            for i in range(3)
        ]

        handler.write_batch(files)
        handler.flush()

        processed = handler.get_processed_files()
        assert len(processed) == 3
        assert all(str(f.full_path) in processed for f in files)

    def test_write_batch_handles_empty_list(self, temp_dir):
        """Test that write_batch handles empty files list."""
        csv_path = temp_dir / "test.csv"
        handler = CSVHandler(csv_path)

        # Should not raise error
        handler.write_batch([])
        assert len(handler._buffer) == 0

    def test_flush_handles_empty_buffer(self, temp_dir):
        """Test that _flush_buffer handles empty buffer."""
        csv_path = temp_dir / "test.csv"
        handler = CSVHandler(csv_path)
        handler.write_header()

        # Should not raise error
        handler._flush_buffer()
        assert len(handler._buffer) == 0

    def test_read_all_handles_invalid_rows(self, temp_dir):
        """Test that read_all handles invalid CSV rows gracefully."""
        csv_path = temp_dir / "test.csv"

        # Create CSV with invalid row - write raw CSV to bypass DictWriter validation
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            f.write("relative_path,filename,file_size,full_path,processed_at\n")
            f.write(
                "invalid,data,missing,fields,row\n"
            )  # Missing required fields for EbookFile.from_dict

        handler = CSVHandler(csv_path)
        files = handler.read_all(temp_dir)
        # Should skip invalid row and return empty list
        assert files == []

    def test_get_last_processed_index_returns_zero_for_nonexistent(self, temp_dir):
        """Test that get_last_processed_index returns 0 for non-existent file."""
        csv_path = temp_dir / "nonexistent.csv"
        handler = CSVHandler(csv_path)
        assert handler.get_last_processed_index() == 0

    def test_get_last_processed_index_returns_correct_count(self, temp_dir):
        """Test that get_last_processed_index returns correct row count."""
        csv_path = temp_dir / "test.csv"
        handler = CSVHandler(csv_path)

        files = [
            EbookFile(
                full_path=temp_dir / f"file{i}.pdf",
                relative_path=Path(f"file{i}.pdf"),
                filename=f"file{i}.pdf",
                file_size=100,
                file_extension=".pdf",
            )
            for i in range(3)
        ]

        handler.write_batch(files)
        handler.flush()

        assert handler.get_last_processed_index() == 3
