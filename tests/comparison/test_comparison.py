"""
Tests for compare_libraries function.
"""

from pathlib import Path

from ebook_calibre_analyzer.comparison import LibraryComparator
from ebook_calibre_analyzer.models import EbookFile, FileCollection


class TestCompareLibraries:
    """Test cases for compare_libraries function."""

    def test_returns_empty_when_all_duplicates(self, temp_dir):
        """Test that compare_libraries returns empty list when all files are duplicates."""
        ebooks_collection = FileCollection()
        calibre_collection = FileCollection()

        # Same file in both - with matching full hash to be true duplicates
        hash_value = b"same_hash"
        file1 = EbookFile(
            full_path=temp_dir / "book1.pdf",
            relative_path=Path("book1.pdf"),
            filename="book1.pdf",
            file_size=100,
            file_extension=".pdf",
            first_1k_hash=b"same_1k",
            full_hash=hash_value,
        )
        file2 = EbookFile(
            full_path=temp_dir / "book1_copy.pdf",
            relative_path=Path("book1_copy.pdf"),
            filename="book1_copy.pdf",
            file_size=100,
            file_extension=".pdf",
            first_1k_hash=b"same_1k",
            full_hash=hash_value,
        )

        ebooks_collection.add_file(file1)
        calibre_collection.add_file(file2)

        comparator = LibraryComparator(ebooks_collection, calibre_collection)
        unique = comparator.find_unique_files()
        # With matching full hash, file1 is a duplicate, so should not be in unique
        assert len(unique) == 0

    def test_returns_all_files_when_calibre_empty(self, temp_dir):
        """Test that compare_libraries returns all files when calibre collection is empty."""
        ebooks_collection = FileCollection()
        calibre_collection = FileCollection()

        file1 = EbookFile(
            full_path=temp_dir / "book1.pdf",
            relative_path=Path("book1.pdf"),
            filename="book1.pdf",
            file_size=100,
            file_extension=".pdf",
        )
        file2 = EbookFile(
            full_path=temp_dir / "book2.pdf",
            relative_path=Path("book2.pdf"),
            filename="book2.pdf",
            file_size=200,
            file_extension=".pdf",
        )

        ebooks_collection.add_file(file1)
        ebooks_collection.add_file(file2)

        comparator = LibraryComparator(ebooks_collection, calibre_collection)
        unique = comparator.find_unique_files()
        assert len(unique) == 2
        assert file1 in unique
        assert file2 in unique

    def test_returns_unique_files_by_size(self, temp_dir):
        """Test that compare_libraries returns unique files by size (Stage 1)."""
        ebooks_collection = FileCollection()
        calibre_collection = FileCollection()

        # Unique size in ebooks
        unique_file = EbookFile(
            full_path=temp_dir / "unique.pdf",
            relative_path=Path("unique.pdf"),
            filename="unique.pdf",
            file_size=100,
            file_extension=".pdf",
        )
        # Different size in calibre
        calibre_file = EbookFile(
            full_path=temp_dir / "calibre.pdf",
            relative_path=Path("calibre.pdf"),
            filename="calibre.pdf",
            file_size=200,
            file_extension=".pdf",
        )

        ebooks_collection.add_file(unique_file)
        calibre_collection.add_file(calibre_file)

        comparator = LibraryComparator(ebooks_collection, calibre_collection)
        unique = comparator.find_unique_files()
        assert len(unique) == 1
        assert unique_file in unique
        assert unique_file.processing_status == "size_checked"

    def test_returns_unique_files_by_size_and_1k_hash(self, temp_dir):
        """Test that compare_libraries returns unique files by (size, 1k_hash) (Stage 2)."""
        ebooks_collection = FileCollection()
        calibre_collection = FileCollection()

        hash1 = b"hash1"
        hash2 = b"hash2"

        # Same size, different 1k hash
        unique_file = EbookFile(
            full_path=temp_dir / "unique.pdf",
            relative_path=Path("unique.pdf"),
            filename="unique.pdf",
            file_size=100,
            file_extension=".pdf",
            first_1k_hash=hash1,
        )
        calibre_file = EbookFile(
            full_path=temp_dir / "calibre.pdf",
            relative_path=Path("calibre.pdf"),
            filename="calibre.pdf",
            file_size=100,
            file_extension=".pdf",
            first_1k_hash=hash2,
        )

        ebooks_collection.add_file(unique_file)
        calibre_collection.add_file(calibre_file)

        comparator = LibraryComparator(ebooks_collection, calibre_collection)
        unique = comparator.find_unique_files()
        assert len(unique) == 1
        assert unique_file in unique
        assert unique_file.processing_status == "1k_hashed"

    def test_returns_unique_files_by_full_hash(self, temp_dir):
        """Test that compare_libraries returns unique files by full_hash (Stage 3)."""
        ebooks_collection = FileCollection()
        calibre_collection = FileCollection()

        hash1 = b"full_hash1"
        hash2 = b"full_hash2"

        # Same size and 1k hash, different full hash
        unique_file = EbookFile(
            full_path=temp_dir / "unique.pdf",
            relative_path=Path("unique.pdf"),
            filename="unique.pdf",
            file_size=100,
            file_extension=".pdf",
            first_1k_hash=b"same_1k",
            full_hash=hash1,
        )
        calibre_file = EbookFile(
            full_path=temp_dir / "calibre.pdf",
            relative_path=Path("calibre.pdf"),
            filename="calibre.pdf",
            file_size=100,
            file_extension=".pdf",
            first_1k_hash=b"same_1k",
            full_hash=hash2,
        )

        ebooks_collection.add_file(unique_file)
        calibre_collection.add_file(calibre_file)

        comparator = LibraryComparator(ebooks_collection, calibre_collection)
        unique = comparator.find_unique_files()
        assert len(unique) == 1
        assert unique_file in unique
        assert unique_file.processing_status == "full_hashed"

    def test_handles_same_size_different_content(self, temp_dir):
        """Test that compare_libraries handles files with same size but different content."""
        ebooks_collection = FileCollection()
        calibre_collection = FileCollection()

        # Same size, different 1k hash - should be considered unique after Stage 2
        file1 = EbookFile(
            full_path=temp_dir / "file1.pdf",
            relative_path=Path("file1.pdf"),
            filename="file1.pdf",
            file_size=100,
            file_extension=".pdf",
            first_1k_hash=b"hash1",
        )
        file2 = EbookFile(
            full_path=temp_dir / "file2.pdf",
            relative_path=Path("file2.pdf"),
            filename="file2.pdf",
            file_size=100,
            file_extension=".pdf",
            first_1k_hash=b"hash2",
        )

        ebooks_collection.add_file(file1)
        calibre_collection.add_file(file2)

        comparator = LibraryComparator(ebooks_collection, calibre_collection)
        unique = comparator.find_unique_files()
        # With different 1k hash, file1 is unique
        assert file1 in unique

    def test_sets_processing_status_correctly(self, temp_dir):
        """Test that compare_libraries sets processing_status correctly for each stage."""
        ebooks_collection = FileCollection()
        calibre_collection = FileCollection()

        file1 = EbookFile(
            full_path=temp_dir / "file1.pdf",
            relative_path=Path("file1.pdf"),
            filename="file1.pdf",
            file_size=100,
            file_extension=".pdf",
        )
        file2 = EbookFile(
            full_path=temp_dir / "file2.pdf",
            relative_path=Path("file2.pdf"),
            filename="file2.pdf",
            file_size=200,
            file_extension=".pdf",
        )

        ebooks_collection.add_file(file1)
        ebooks_collection.add_file(file2)
        calibre_collection.add_file(file2)

        comparator = LibraryComparator(ebooks_collection, calibre_collection)
        comparator.find_unique_files()
        assert file1.processing_status == "size_checked"
        assert file2.processing_status == "size_checked"

    def test_handles_files_without_hashes(self, temp_dir):
        """Test that compare_libraries handles files without hashes (skips stages 2/3)."""
        ebooks_collection = FileCollection()
        calibre_collection = FileCollection()

        # Different sizes - should be unique at Stage 1
        file1 = EbookFile(
            full_path=temp_dir / "file1.pdf",
            relative_path=Path("file1.pdf"),
            filename="file1.pdf",
            file_size=100,
            file_extension=".pdf",
            # No hashes
        )
        file2 = EbookFile(
            full_path=temp_dir / "file2.pdf",
            relative_path=Path("file2.pdf"),
            filename="file2.pdf",
            file_size=200,  # Different size
            file_extension=".pdf",
            # No hashes
        )

        ebooks_collection.add_file(file1)
        calibre_collection.add_file(file2)

        comparator = LibraryComparator(ebooks_collection, calibre_collection)
        unique = comparator.find_unique_files()
        # Different sizes, so file1 is unique at Stage 1
        assert file1 in unique

    def test_skips_stage3_when_full_hash_none(self, temp_dir):
        """Test that compare_libraries skips Stage 3 when full_hash is None."""
        ebooks_collection = FileCollection()
        calibre_collection = FileCollection()

        # Same size and 1k hash, but no full hash - should skip Stage 3
        file1 = EbookFile(
            full_path=temp_dir / "file1.pdf",
            relative_path=Path("file1.pdf"),
            filename="file1.pdf",
            file_size=100,
            file_extension=".pdf",
            first_1k_hash=b"same_1k",
            full_hash=None,  # No full hash - triggers continue on line 79
        )
        file2 = EbookFile(
            full_path=temp_dir / "file2.pdf",
            relative_path=Path("file2.pdf"),
            filename="file2.pdf",
            file_size=100,
            file_extension=".pdf",
            first_1k_hash=b"same_1k",
            full_hash=None,
        )

        ebooks_collection.add_file(file1)
        calibre_collection.add_file(file2)

        comparator = LibraryComparator(ebooks_collection, calibre_collection)
        comparator.find_unique_files()
        # Without full hash, Stage 3 is skipped (continue on line 79)
        # File1 should not be in unique (it matched in Stage 2, but can't verify in Stage 3)
        # The continue path should be executed
        assert file1.processing_status == "1k_hashed"  # Should remain at 1k_hashed
