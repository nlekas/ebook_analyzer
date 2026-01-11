"""
Tests for full copy workflow.
"""

from pathlib import Path

from ebook_calibre_analyzer.copier import FileCopier
from ebook_calibre_analyzer.csv_handler import CSVHandler
from ebook_calibre_analyzer.models import EbookFile


class TestCopyWorkflow:
    """Test cases for complete copy workflow."""

    def test_complete_copy_from_csv_to_target(self, temp_dir):
        """Test complete copy from CSV to target."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        source.mkdir()

        # Create source file
        source_file = source / "book.pdf"
        source_file.write_bytes(b"content")

        # Create CSV
        handler = CSVHandler(csv_path)
        file = EbookFile(
            full_path=source_file,
            relative_path=Path("book.pdf"),
            filename="book.pdf",
            file_size=len(b"content"),
            file_extension=".pdf",
        )
        handler.write_batch([file])
        handler.flush()

        # Copy
        copier = FileCopier(csv_path, source, target)
        stats = copier.copy_all()

        assert stats["total"] == 1
        assert stats["success"] == 1
        assert (target / "book.pdf").exists()
        assert (target / "book.pdf").read_bytes() == b"content"

    def test_handles_filename_conflicts(self, temp_dir):
        """Test that copy handles filename conflicts."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        source.mkdir()
        target.mkdir()

        # Create existing file in target
        (target / "book.pdf").write_bytes(b"existing")

        # Create source file
        source_file = source / "book.pdf"
        source_file.write_bytes(b"new content")

        # Create CSV
        handler = CSVHandler(csv_path)
        file = EbookFile(
            full_path=source_file,
            relative_path=Path("book.pdf"),
            filename="book.pdf",
            file_size=len(b"new content"),
            file_extension=".pdf",
        )
        handler.write_batch([file])
        handler.flush()

        # Copy with rename
        copier = FileCopier(csv_path, source, target, conflict_handling="rename")
        stats = copier.copy_all()

        assert stats["success"] == 1
        # Original should still exist
        assert (target / "book.pdf").exists()
        # New file should have different name
        copied_files = list(target.glob("book_*.pdf"))
        assert len(copied_files) > 0

    def test_preserves_file_metadata(self, temp_dir):
        """Test that copy preserves file metadata."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        source.mkdir()

        source_file = source / "book.pdf"
        source_file.write_bytes(b"content")

        # Create CSV
        handler = CSVHandler(csv_path)
        file = EbookFile(
            full_path=source_file,
            relative_path=Path("book.pdf"),
            filename="book.pdf",
            file_size=len(b"content"),
            file_extension=".pdf",
        )
        handler.write_batch([file])
        handler.flush()

        # Copy
        copier = FileCopier(csv_path, source, target)
        copier.copy_all()

        target_file = target / "book.pdf"
        assert target_file.exists()
        # shutil.copy2 preserves metadata
        assert target_file.stat().st_size == source_file.stat().st_size

    def test_creates_flat_structure_correctly(self, temp_dir):
        """Test that copy creates flat structure correctly."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        source.mkdir()

        # Create nested source file
        nested_file = source / "subdir" / "nested" / "book.pdf"
        nested_file.parent.mkdir(parents=True)
        nested_file.write_bytes(b"content")

        # Create CSV
        handler = CSVHandler(csv_path)
        file = EbookFile(
            full_path=nested_file,
            relative_path=Path("subdir/nested/book.pdf"),
            filename="book.pdf",
            file_size=len(b"content"),
            file_extension=".pdf",
        )
        handler.write_batch([file])
        handler.flush()

        # Copy
        copier = FileCopier(csv_path, source, target)
        copier.copy_all()

        # Should be in target root, not nested
        assert (target / "book.pdf").exists()
        assert not (target / "subdir").exists()
