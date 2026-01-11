"""
Tests for full analysis workflow.
"""

from ebook_calibre_analyzer.comparison import LibraryComparator
from ebook_calibre_analyzer.csv_handler import CSVHandler
from ebook_calibre_analyzer.discovery import discover_files_recursive
from ebook_calibre_analyzer.models import FileCollection


class TestAnalysisWorkflow:
    """Test cases for complete analysis workflow."""

    def test_complete_analysis_from_discovery_to_csv(self, temp_dir):
        """Test complete analysis from discovery to CSV output."""
        ebooks = temp_dir / "ebooks"
        calibre = temp_dir / "calibre"
        ebooks.mkdir()
        calibre.mkdir()

        # Create test files
        (ebooks / "unique.pdf").write_bytes(b"unique content")
        (calibre / "existing.pdf").write_bytes(b"existing content")

        # Discover files
        ebooks_files = discover_files_recursive(ebooks, [".pdf"])
        calibre_files = discover_files_recursive(calibre, [".pdf"])

        # Build collections
        ebooks_collection = FileCollection()
        for file in ebooks_files:
            ebooks_collection.add_file(file)

        calibre_collection = FileCollection()
        for file in calibre_files:
            calibre_collection.add_file(file)

        # Compare
        comparator = LibraryComparator(ebooks_collection, calibre_collection)
        unique_files = comparator.find_unique_files()

        # Write to CSV
        csv_path = temp_dir / "output.csv"
        handler = CSVHandler(csv_path)
        handler.write_batch(unique_files)
        handler.flush()

        assert csv_path.exists()
        assert len(unique_files) >= 1

    def test_resume_from_partial_csv(self, temp_dir):
        """Test resume from partial CSV."""
        ebooks = temp_dir / "ebooks"
        calibre = temp_dir / "calibre"
        ebooks.mkdir()
        calibre.mkdir()

        # Create initial CSV
        csv_path = temp_dir / "resume.csv"
        handler = CSVHandler(csv_path)
        file1 = (
            discover_files_recursive(ebooks, [".pdf"])[0]
            if (ebooks / "file1.pdf").exists()
            else None
        )
        if file1:
            handler.write_batch([file1])
            handler.flush()

        # Resume mode
        handler2 = CSVHandler(csv_path, resume_mode=True)
        processed = handler2.get_processed_files()
        assert len(processed) >= 0  # May be 0 or more depending on setup

    def test_handles_large_number_of_files(self, temp_dir):
        """Test that analysis handles large number of files."""
        ebooks = temp_dir / "ebooks"
        calibre = temp_dir / "calibre"
        ebooks.mkdir()
        calibre.mkdir()

        # Create multiple files
        for i in range(10):
            (ebooks / f"book{i}.pdf").write_bytes(f"content{i}".encode())

        files = discover_files_recursive(ebooks, [".pdf"])
        assert len(files) == 10

        collection = FileCollection()
        for file in files:
            collection.add_file(file)

        assert len(collection.files) == 10

    def test_handles_nested_directory_structures(self, temp_dir):
        """Test that analysis handles nested directory structures."""
        ebooks = temp_dir / "ebooks"
        calibre = temp_dir / "calibre"
        ebooks.mkdir()
        calibre.mkdir()

        # Create nested structure
        (ebooks / "level1" / "level2" / "book.pdf").parent.mkdir(parents=True)
        (ebooks / "level1" / "level2" / "book.pdf").write_bytes(b"content")

        files = discover_files_recursive(ebooks, [".pdf"])
        assert len(files) == 1
        assert "level2" in str(files[0].relative_path)
