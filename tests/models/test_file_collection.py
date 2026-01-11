"""
Tests for FileCollection class.
"""

from pathlib import Path

from ebook_calibre_analyzer.models import EbookFile, FileCollection


class TestFileCollection:
    """Test cases for FileCollection class."""

    def test_init_creates_empty_collection(self):
        """Test that __init__ initializes empty collection."""
        collection = FileCollection()
        assert len(collection.files) == 0

    def test_init_initializes_lookup_dicts(self):
        """Test that __init__ initializes all lookup dictionaries as empty."""
        collection = FileCollection()
        assert len(collection.by_size) == 0
        assert len(collection.by_size_and_1k) == 0
        assert len(collection.by_full_hash) == 0

    def test_add_file_adds_to_files_list(self, sample_ebook_file):
        """Test that add_file adds file to files list."""
        collection = FileCollection()
        collection.add_file(sample_ebook_file)
        assert sample_ebook_file in collection.files
        assert len(collection.files) == 1

    def test_add_file_adds_to_by_size(self, sample_ebook_file):
        """Test that add_file adds file to by_size dictionary."""
        collection = FileCollection()
        collection.add_file(sample_ebook_file)
        size = sample_ebook_file.file_size
        assert sample_ebook_file in collection.by_size[size]

    def test_add_file_adds_to_by_size_and_1k(self, temp_dir):
        """Test that add_file adds file to by_size_and_1k when first_1k_hash is set."""
        file = EbookFile(
            full_path=temp_dir / "test.pdf",
            relative_path=Path("test.pdf"),
            filename="test.pdf",
            file_size=100,
            file_extension=".pdf",
            first_1k_hash=b"test_hash",
        )
        collection = FileCollection()
        collection.add_file(file)
        size = file.file_size
        key = (size, b"test_hash")
        assert file in collection.by_size_and_1k[key]

    def test_add_file_adds_to_by_full_hash(self, temp_dir):
        """Test that add_file adds file to by_full_hash when full_hash is set."""
        file = EbookFile(
            full_path=temp_dir / "test.pdf",
            relative_path=Path("test.pdf"),
            filename="test.pdf",
            file_size=100,
            file_extension=".pdf",
            full_hash=b"full_hash_value",
        )
        collection = FileCollection()
        collection.add_file(file)
        assert collection.by_full_hash[b"full_hash_value"] == file

    def test_add_file_handles_multiple_same_size(self, temp_dir):
        """Test that add_file handles multiple files with same size."""
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
            file_size=100,
            file_extension=".pdf",
        )
        collection = FileCollection()
        collection.add_file(file1)
        collection.add_file(file2)
        assert len(collection.by_size[100]) == 2
        assert file1 in collection.by_size[100]
        assert file2 in collection.by_size[100]

    def test_add_file_handles_multiple_same_size_and_1k(self, temp_dir):
        """Test that add_file handles multiple files with same (size, 1k_hash)."""
        hash_1k = b"same_hash"
        file1 = EbookFile(
            full_path=temp_dir / "file1.pdf",
            relative_path=Path("file1.pdf"),
            filename="file1.pdf",
            file_size=100,
            file_extension=".pdf",
            first_1k_hash=hash_1k,
        )
        file2 = EbookFile(
            full_path=temp_dir / "file2.pdf",
            relative_path=Path("file2.pdf"),
            filename="file2.pdf",
            file_size=100,
            file_extension=".pdf",
            first_1k_hash=hash_1k,
        )
        collection = FileCollection()
        collection.add_file(file1)
        collection.add_file(file2)
        key = (100, hash_1k)
        assert len(collection.by_size_and_1k[key]) == 2

    def test_add_file_handles_duplicate_full_hash(self, temp_dir):
        """Test that add_file handles duplicate full_hash (overwrites)."""
        hash_value = b"duplicate_hash"
        file1 = EbookFile(
            full_path=temp_dir / "file1.pdf",
            relative_path=Path("file1.pdf"),
            filename="file1.pdf",
            file_size=100,
            file_extension=".pdf",
            full_hash=hash_value,
        )
        file2 = EbookFile(
            full_path=temp_dir / "file2.pdf",
            relative_path=Path("file2.pdf"),
            filename="file2.pdf",
            file_size=100,
            file_extension=".pdf",
            full_hash=hash_value,
        )
        collection = FileCollection()
        collection.add_file(file1)
        collection.add_file(file2)
        # Last file should overwrite
        assert collection.by_full_hash[hash_value] == file2

    def test_get_files_by_size_returns_empty_for_nonexistent(self):
        """Test that get_files_by_size returns empty list for non-existent size."""
        collection = FileCollection()
        assert collection.get_files_by_size(999) == []

    def test_get_files_by_size_returns_matching_files(self, sample_ebook_file):
        """Test that get_files_by_size returns all files with matching size."""
        collection = FileCollection()
        collection.add_file(sample_ebook_file)
        size = sample_ebook_file.file_size
        result = collection.get_files_by_size(size)
        assert sample_ebook_file in result
        assert len(result) == 1

    def test_get_files_by_size_handles_multiple_sizes(self, temp_dir):
        """Test that get_files_by_size returns correct files when multiple sizes exist."""
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
        collection = FileCollection()
        collection.add_file(file1)
        collection.add_file(file2)
        assert len(collection.get_files_by_size(100)) == 1
        assert len(collection.get_files_by_size(200)) == 1
        assert file1 in collection.get_files_by_size(100)
        assert file2 in collection.get_files_by_size(200)

    def test_get_files_by_size_and_1k_returns_empty_for_nonexistent(self):
        """Test that get_files_by_size_and_1k returns empty list for non-existent combination."""
        collection = FileCollection()
        assert collection.get_files_by_size_and_1k(100, b"nonexistent") == []

    def test_get_files_by_size_and_1k_returns_matching_files(self, temp_dir):
        """Test that get_files_by_size_and_1k returns all files with matching size and 1k hash."""
        hash_1k = b"test_hash"
        file = EbookFile(
            full_path=temp_dir / "test.pdf",
            relative_path=Path("test.pdf"),
            filename="test.pdf",
            file_size=100,
            file_extension=".pdf",
            first_1k_hash=hash_1k,
        )
        collection = FileCollection()
        collection.add_file(file)
        result = collection.get_files_by_size_and_1k(100, hash_1k)
        assert file in result
        assert len(result) == 1

    def test_get_file_by_full_hash_returns_none_for_nonexistent(self):
        """Test that get_file_by_full_hash returns None for non-existent hash."""
        collection = FileCollection()
        assert collection.get_file_by_full_hash(b"nonexistent") is None

    def test_get_file_by_full_hash_returns_correct_file(self, temp_dir):
        """Test that get_file_by_full_hash returns correct file for existing hash."""
        hash_value = b"test_hash"
        file = EbookFile(
            full_path=temp_dir / "test.pdf",
            relative_path=Path("test.pdf"),
            filename="test.pdf",
            file_size=100,
            file_extension=".pdf",
            full_hash=hash_value,
        )
        collection = FileCollection()
        collection.add_file(file)
        assert collection.get_file_by_full_hash(hash_value) == file

    def test_get_unique_sizes_returns_empty_set(self):
        """Test that get_unique_sizes returns empty set for empty collection."""
        collection = FileCollection()
        assert collection.get_unique_sizes() == set()

    def test_get_unique_sizes_returns_all_sizes(self, temp_dir):
        """Test that get_unique_sizes returns set of all unique sizes."""
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
        collection = FileCollection()
        collection.add_file(file1)
        collection.add_file(file2)
        sizes = collection.get_unique_sizes()
        assert sizes == {100, 200}
