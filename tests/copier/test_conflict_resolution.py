"""
Tests for conflict resolution in FileCopier.
"""

from pathlib import Path

from ebook_calibre_analyzer.copier import FileCopier
from ebook_calibre_analyzer.models import EbookFile


class TestConflictResolution:
    """Test cases for conflict resolution."""

    def test_resolve_filename_conflict_generates_new_name(self, temp_dir):
        """Test that _resolve_filename_conflict generates new filename with random suffix."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        source.mkdir()
        target.mkdir()

        # Create existing file in target
        existing = target / "book.pdf"
        existing.write_bytes(b"existing")

        copier = FileCopier(csv_path, source, target, conflict_handling="rename")

        # Create source file
        source_file = source / "book.pdf"
        source_file.write_bytes(b"new content")

        file = EbookFile(
            full_path=source_file,
            relative_path=Path("book.pdf"),
            filename="book.pdf",
            file_size=len(b"new content"),
            file_extension=".pdf",
        )

        result = copier.copy_file(file)
        assert result["success"] is True
        # Should have a different name
        assert result["target"] != str(existing)
        assert "book_" in result["target"]

    def test_resolve_filename_conflict_format(self, temp_dir):
        """Test that _resolve_filename_conflict format: stem_randomwordNN.ext."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        source.mkdir()
        target.mkdir()

        existing = target / "book.pdf"
        existing.write_bytes(b"existing")

        copier = FileCopier(csv_path, source, target, conflict_handling="rename")

        source_file = source / "book.pdf"
        source_file.write_bytes(b"new")

        file = EbookFile(
            full_path=source_file,
            relative_path=Path("book.pdf"),
            filename="book.pdf",
            file_size=len(b"new"),
            file_extension=".pdf",
        )

        result = copier.copy_file(file)
        target_path = Path(result["target"])
        # Format: book_randomwordNN.pdf
        assert target_path.stem.startswith("book_")
        assert target_path.suffix == ".pdf"
        assert len(target_path.stem.split("_")) == 2  # book and randomwordNN

    def test_resolve_filename_conflict_returns_unique_path(self, temp_dir):
        """Test that _resolve_filename_conflict returns path that doesn't exist."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        source.mkdir()
        target.mkdir()

        existing = target / "book.pdf"
        existing.write_bytes(b"existing")

        copier = FileCopier(csv_path, source, target, conflict_handling="rename")

        source_file = source / "book.pdf"
        source_file.write_bytes(b"new")

        file = EbookFile(
            full_path=source_file,
            relative_path=Path("book.pdf"),
            filename="book.pdf",
            file_size=len(b"new"),
            file_extension=".pdf",
        )

        result = copier.copy_file(file)
        target_path = Path(result["target"])
        assert not existing.exists() or target_path != existing
        # The new file should exist
        assert target_path.exists()

    def test_copy_file_handles_rename_mode(self, temp_dir):
        """Test that copy_file handles conflict with rename mode."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        source.mkdir()
        target.mkdir()

        existing = target / "book.pdf"
        existing.write_bytes(b"existing")

        copier = FileCopier(csv_path, source, target, conflict_handling="rename")

        source_file = source / "book.pdf"
        source_file.write_bytes(b"new")

        file = EbookFile(
            full_path=source_file,
            relative_path=Path("book.pdf"),
            filename="book.pdf",
            file_size=len(b"new"),
            file_extension=".pdf",
        )

        result = copier.copy_file(file)
        assert result["success"] is True
        assert Path(result["target"]).exists()
        assert Path(result["target"]) != existing

    def test_copy_file_handles_skip_mode(self, temp_dir):
        """Test that copy_file handles conflict with skip mode."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        source.mkdir()
        target.mkdir()

        existing = target / "book.pdf"
        existing.write_bytes(b"existing")

        copier = FileCopier(csv_path, source, target, conflict_handling="skip")

        source_file = source / "book.pdf"
        source_file.write_bytes(b"new")

        file = EbookFile(
            full_path=source_file,
            relative_path=Path("book.pdf"),
            filename="book.pdf",
            file_size=len(b"new"),
            file_extension=".pdf",
        )

        result = copier.copy_file(file)
        assert result["success"] is False
        assert "skipping" in result["message"].lower()
        # Original file should still exist with original content
        assert existing.read_bytes() == b"existing"

    def test_copy_file_handles_overwrite_mode(self, temp_dir):
        """Test that copy_file handles conflict with overwrite mode."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        source.mkdir()
        target.mkdir()

        existing = target / "book.pdf"
        existing.write_bytes(b"existing")

        copier = FileCopier(csv_path, source, target, conflict_handling="overwrite")

        source_file = source / "book.pdf"
        source_file.write_bytes(b"new content")

        file = EbookFile(
            full_path=source_file,
            relative_path=Path("book.pdf"),
            filename="book.pdf",
            file_size=len(b"new content"),
            file_extension=".pdf",
        )

        result = copier.copy_file(file)
        assert result["success"] is True
        assert existing.read_bytes() == b"new content"
