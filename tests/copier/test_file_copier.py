"""
Tests for FileCopier class.
"""

from pathlib import Path

import pytest

from ebook_calibre_analyzer.copier import FileCopier
from ebook_calibre_analyzer.csv_handler import CSVHandler
from ebook_calibre_analyzer.models import EbookFile


class TestFileCopier:
    """Test cases for FileCopier class."""

    def test_init_sets_paths_correctly(self, temp_dir):
        """Test that __init__ initializes with provided paths."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"

        copier = FileCopier(csv_path, source, target)
        assert copier.csv_path == csv_path
        assert copier.source_base == source
        assert copier.target_folder == target

    def test_init_raises_value_error_for_invalid_conflict_handling(self, temp_dir):
        """Test that __init__ raises ValueError for invalid conflict_handling."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"

        with pytest.raises(ValueError):
            FileCopier(csv_path, source, target, conflict_handling="invalid")

    def test_load_files_from_csv_loads_files(self, temp_dir):
        """Test that load_files_from_csv loads files from CSV."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"

        # Create CSV with files
        handler = CSVHandler(csv_path)
        file1 = EbookFile(
            full_path=source / "file1.pdf",
            relative_path=Path("file1.pdf"),
            filename="file1.pdf",
            file_size=100,
            file_extension=".pdf",
        )
        handler.write_batch([file1])
        handler.flush()

        copier = FileCopier(csv_path, source, target)
        files = copier.load_files_from_csv()
        assert len(files) == 1
        assert files[0].filename == "file1.pdf"

    def test_copy_file_returns_error_when_source_missing(self, temp_dir):
        """Test that copy_file returns error when source file doesn't exist."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        target.mkdir()

        copier = FileCopier(csv_path, source, target)

        file = EbookFile(
            full_path=source / "nonexistent.pdf",
            relative_path=Path("nonexistent.pdf"),
            filename="nonexistent.pdf",
            file_size=100,
            file_extension=".pdf",
        )

        result = copier.copy_file(file)
        assert result["success"] is False
        assert "does not exist" in result["message"]

    def test_copy_file_copies_to_target_root(self, temp_dir):
        """Test that copy_file copies file to target root (flat structure)."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        source.mkdir()
        target.mkdir()

        # Create source file
        source_file = source / "subdir" / "book.pdf"
        source_file.parent.mkdir(parents=True)
        source_file.write_bytes(b"content")

        copier = FileCopier(csv_path, source, target)

        file = EbookFile(
            full_path=source_file,
            relative_path=Path("subdir/book.pdf"),
            filename="book.pdf",
            file_size=len(b"content"),
            file_extension=".pdf",
        )

        result = copier.copy_file(file)
        assert result["success"] is True
        # Should be in target root, not subdir
        assert (target / "book.pdf").exists()
        assert not (target / "subdir").exists()

    def test_copy_file_creates_target_directory(self, temp_dir):
        """Test that copy_file creates target directory if needed."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "new_target"
        source.mkdir()

        source_file = source / "book.pdf"
        source_file.write_bytes(b"content")

        copier = FileCopier(csv_path, source, target)

        file = EbookFile(
            full_path=source_file,
            relative_path=Path("book.pdf"),
            filename="book.pdf",
            file_size=len(b"content"),
            file_extension=".pdf",
        )

        result = copier.copy_file(file)
        assert result["success"] is True
        assert target.exists()
        assert (target / "book.pdf").exists()

    def test_copy_file_handles_dry_run_mode(self, temp_dir):
        """Test that copy_file returns dry-run dict when dry_run=True."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        source.mkdir()

        source_file = source / "book.pdf"
        source_file.write_bytes(b"content")

        copier = FileCopier(csv_path, source, target)

        file = EbookFile(
            full_path=source_file,
            relative_path=Path("book.pdf"),
            filename="book.pdf",
            file_size=len(b"content"),
            file_extension=".pdf",
        )

        result = copier.copy_file(file, dry_run=True)
        assert result["success"] is True
        assert "Would copy" in result["message"]
        assert not (target / "book.pdf").exists()  # File not actually copied

    def test_copy_all_copies_all_files(self, temp_dir):
        """Test that copy_all copies all files from CSV."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        source.mkdir()

        # Create CSV
        handler = CSVHandler(csv_path)
        files = []
        for i in range(3):
            source_file = source / f"file{i}.pdf"
            source_file.write_bytes(f"content{i}".encode())
            file = EbookFile(
                full_path=source_file,
                relative_path=Path(f"file{i}.pdf"),
                filename=f"file{i}.pdf",
                file_size=len(f"content{i}".encode()),
                file_extension=".pdf",
            )
            files.append(file)
        handler.write_batch(files)
        handler.flush()

        copier = FileCopier(csv_path, source, target)
        stats = copier.copy_all()

        assert stats["total"] == 3
        assert stats["success"] == 3
        assert len(stats["results"]) == 3

    def test_copy_all_returns_correct_statistics(self, temp_dir):
        """Test that copy_all returns correct statistics (total, success, failed, skipped)."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        source.mkdir()

        # Create CSV with mix of existing and missing files
        handler = CSVHandler(csv_path)
        file1 = EbookFile(
            full_path=source / "file1.pdf",
            relative_path=Path("file1.pdf"),
            filename="file1.pdf",
            file_size=100,
            file_extension=".pdf",
        )
        file1.full_path.write_bytes(b"content1")

        file2 = EbookFile(
            full_path=source / "file2.pdf",
            relative_path=Path("file2.pdf"),
            filename="file2.pdf",
            file_size=100,
            file_extension=".pdf",
        )
        # file2 doesn't exist

        handler.write_batch([file1, file2])
        handler.flush()

        copier = FileCopier(csv_path, source, target, conflict_handling="skip")
        stats = copier.copy_all()

        assert stats["total"] == 2
        assert stats["success"] == 1
        assert stats["failed"] == 1
        assert "total" in stats
        assert "success" in stats
        assert "failed" in stats
        assert "skipped" in stats
        assert "results" in stats

    def test_copy_file_handles_copy_exception(self, temp_dir):
        """Test that copy_file handles exceptions during copy operation."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        source.mkdir()
        target.mkdir()

        source_file = source / "book.pdf"
        source_file.write_bytes(b"content")

        copier = FileCopier(csv_path, source, target)

        file = EbookFile(
            full_path=source_file,
            relative_path=Path("book.pdf"),
            filename="book.pdf",
            file_size=len(b"content"),
            file_extension=".pdf",
        )

        # Mock shutil.copy2 to raise an exception
        from unittest.mock import patch

        with patch("ebook_calibre_analyzer.copier.shutil.copy2") as mock_copy:
            mock_copy.side_effect = OSError("Permission denied")
            result = copier.copy_file(file)
            assert result["success"] is False
            assert "Error copying" in result["message"]

    def test_resolve_filename_conflict_fallback_loop(self, temp_dir):
        """Test that _resolve_filename_conflict uses fallback counter when random attempts fail."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        source.mkdir()
        target.mkdir()

        # Create the target file that will conflict
        (target / "book.pdf").write_bytes(b"existing")

        # Mock generate_random_suffix to always return the same value to force fallback
        from unittest.mock import patch

        # Create 100 files with the same random suffix pattern to exhaust random attempts
        # Then the fallback counter should kick in
        with patch("ebook_calibre_analyzer.copier.generate_random_suffix") as mock_suffix:
            # Make it return a fixed value that will always conflict
            mock_suffix.return_value = "test00"
            # Create a file with that suffix so it conflicts
            (target / "book_test00.pdf").write_bytes(b"existing")

            copier = FileCopier(csv_path, source, target, conflict_handling="rename")

            source_file = source / "book.pdf"
            source_file.write_bytes(b"content")

            file = EbookFile(
                full_path=source_file,
                relative_path=Path("book.pdf"),
                filename="book.pdf",
                file_size=len(b"content"),
                file_extension=".pdf",
            )

            # This should trigger the fallback counter loop after 100 attempts
            result = copier.copy_file(file)
            assert result["success"] is True
            # Should have used counter fallback (book_1.pdf, book_2.pdf, etc.)
            assert "book_1.pdf" in result["target"] or "book_2.pdf" in result["target"]

    def test_copy_all_handles_skip_mode(self, temp_dir):
        """Test that copy_all correctly identifies skipped files."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        source.mkdir()
        target.mkdir()

        # Create existing file in target
        (target / "book.pdf").write_bytes(b"existing")

        handler = CSVHandler(csv_path)
        source_file = source / "book.pdf"
        source_file.write_bytes(b"new content")

        file = EbookFile(
            full_path=source_file,
            relative_path=Path("book.pdf"),
            filename="book.pdf",
            file_size=len(b"new content"),
            file_extension=".pdf",
        )
        handler.write_batch([file])
        handler.flush()

        copier = FileCopier(csv_path, source, target, conflict_handling="skip")
        stats = copier.copy_all()

        assert stats["total"] == 1
        assert stats["skipped"] == 1
        assert stats["success"] == 0
