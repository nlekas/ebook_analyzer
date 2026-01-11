"""
Tests for end-to-end workflows.
"""

from pathlib import Path

from ebook_calibre_analyzer.comparison import LibraryComparator
from ebook_calibre_analyzer.copier import FileCopier
from ebook_calibre_analyzer.csv_handler import CSVHandler
from ebook_calibre_analyzer.discovery import discover_files_recursive
from ebook_calibre_analyzer.models import EbookFile, FileCollection


class TestEndToEnd:
    """Test cases for end-to-end workflows."""

    def test_analyze_review_copy_workflow(self, temp_dir):
        """Test Analyze → Review CSV → Copy workflow."""
        ebooks = temp_dir / "ebooks"
        calibre = temp_dir / "calibre"
        target = temp_dir / "target"
        ebooks.mkdir()
        calibre.mkdir()

        # Create files
        (ebooks / "unique1.pdf").write_bytes(b"unique1")
        (ebooks / "unique2.pdf").write_bytes(b"unique2")
        (calibre / "existing.pdf").write_bytes(b"existing")

        # Analyze
        ebooks_files = discover_files_recursive(ebooks, [".pdf"])
        calibre_files = discover_files_recursive(calibre, [".pdf"])

        ebooks_collection = FileCollection()
        for file in ebooks_files:
            ebooks_collection.add_file(file)

        calibre_collection = FileCollection()
        for file in calibre_files:
            calibre_collection.add_file(file)

        comparator = LibraryComparator(ebooks_collection, calibre_collection)
        unique_files = comparator.find_unique_files()

        # Write CSV
        csv_path = temp_dir / "output.csv"
        handler = CSVHandler(csv_path)
        handler.write_batch(unique_files)
        handler.flush()

        # Copy
        copier = FileCopier(csv_path, ebooks, target)
        stats = copier.copy_all()

        assert stats["success"] >= 1
        assert csv_path.exists()

    def test_resume_analysis_after_interruption(self, temp_dir):
        """Test resume analysis after interruption."""
        ebooks = temp_dir / "ebooks"
        calibre = temp_dir / "calibre"
        ebooks.mkdir()
        calibre.mkdir()

        # Create a real file first
        (ebooks / "file1.pdf").write_bytes(b"content")

        # Create partial CSV
        csv_path = temp_dir / "partial.csv"
        handler = CSVHandler(csv_path)
        file1 = EbookFile(
            full_path=ebooks / "file1.pdf",
            relative_path=Path("file1.pdf"),
            filename="file1.pdf",
            file_size=len(b"content"),
            file_extension=".pdf",
        )
        handler.write_batch([file1])
        handler.flush()

        # Resume
        handler2 = CSVHandler(csv_path, resume_mode=True)
        processed = handler2.get_processed_files()
        assert len(processed) == 1

    def test_copy_files_from_analysis_csv(self, temp_dir):
        """Test copy files from analysis CSV."""
        ebooks = temp_dir / "ebooks"
        target = temp_dir / "target"
        ebooks.mkdir()

        # Create file and CSV
        source_file = ebooks / "book.pdf"
        content = b"content"
        source_file.write_bytes(content)

        csv_path = temp_dir / "analysis.csv"
        handler = CSVHandler(csv_path)
        file = EbookFile(
            full_path=source_file,
            relative_path=Path("book.pdf"),
            filename="book.pdf",
            file_size=len(content),
            file_extension=".pdf",
        )
        handler.write_batch([file])
        handler.flush()

        # Copy from analysis CSV
        copier = FileCopier(csv_path, ebooks, target)
        stats = copier.copy_all()

        assert stats["success"] == 1
        assert (target / "book.pdf").exists()
        assert (target / "book.pdf").read_bytes() == content

    def test_verify_copied_files_match_source(self, temp_dir):
        """Test verify copied files match source."""
        csv_path = temp_dir / "test.csv"
        source = temp_dir / "source"
        target = temp_dir / "target"
        source.mkdir()

        content = b"test content"
        source_file = source / "book.pdf"
        source_file.write_bytes(content)

        # Create CSV
        handler = CSVHandler(csv_path)
        file = EbookFile(
            full_path=source_file,
            relative_path=Path("book.pdf"),
            filename="book.pdf",
            file_size=len(content),
            file_extension=".pdf",
        )
        handler.write_batch([file])
        handler.flush()

        # Copy
        copier = FileCopier(csv_path, source, target)
        copier.copy_all()

        # Verify
        target_file = target / "book.pdf"
        assert target_file.exists()
        assert target_file.read_bytes() == content
        assert target_file.stat().st_size == source_file.stat().st_size
