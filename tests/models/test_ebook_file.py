"""
Tests for EbookFile class.
"""

from pathlib import Path

import pytest

from ebook_calibre_analyzer.models import EbookFile


class TestEbookFile:
    """Test cases for EbookFile class."""

    def test_get_size_hash_returns_file_size_when_none(self, sample_ebook_file):
        """Test that get_size_hash returns file_size when size_hash is None."""
        sample_ebook_file.size_hash = None
        assert sample_ebook_file.get_size_hash() == sample_ebook_file.file_size

    def test_get_size_hash_sets_size_hash_when_none(self, sample_ebook_file):
        """Test that get_size_hash sets size_hash to file_size when None."""
        sample_ebook_file.size_hash = None
        sample_ebook_file.get_size_hash()
        assert sample_ebook_file.size_hash == sample_ebook_file.file_size

    def test_get_size_hash_returns_cached_value(self, sample_ebook_file):
        """Test that get_size_hash returns cached size_hash when already set."""
        sample_ebook_file.size_hash = 999
        assert sample_ebook_file.get_size_hash() == 999
        assert sample_ebook_file.get_size_hash() == 999  # Should return same value

    def test_get_size_hash_handles_zero_size(self, temp_dir):
        """Test that get_size_hash handles zero file size."""
        file = EbookFile(
            full_path=temp_dir / "empty.pdf",
            relative_path=Path("empty.pdf"),
            filename="empty.pdf",
            file_size=0,
            file_extension=".pdf",
        )
        assert file.get_size_hash() == 0

    def test_get_size_hash_handles_large_size(self, temp_dir):
        """Test that get_size_hash handles very large file sizes."""
        large_size = 500_000_000_000  # 500GB
        file = EbookFile(
            full_path=temp_dir / "large.pdf",
            relative_path=Path("large.pdf"),
            filename="large.pdf",
            file_size=large_size,
            file_extension=".pdf",
        )
        assert file.get_size_hash() == large_size

    def test_to_dict_returns_all_keys(self, sample_ebook_file):
        """Test that to_dict returns dictionary with all required keys."""
        result = sample_ebook_file.to_dict()
        required_keys = {"relative_path", "filename", "file_size", "full_path"}
        assert set(result.keys()) == required_keys

    def test_to_dict_converts_paths_to_strings(self, sample_ebook_file):
        """Test that to_dict converts Path objects to strings correctly."""
        result = sample_ebook_file.to_dict()
        assert isinstance(result["relative_path"], str)
        assert isinstance(result["full_path"], str)

    def test_to_dict_handles_relative_paths(self, temp_dir):
        """Test that to_dict handles relative paths with subdirectories."""
        file = EbookFile(
            full_path=temp_dir / "subdir" / "book.pdf",
            relative_path=Path("subdir/book.pdf"),
            filename="book.pdf",
            file_size=100,
            file_extension=".pdf",
        )
        result = file.to_dict()
        assert result["relative_path"] == "subdir/book.pdf"

    def test_to_dict_handles_path_separators(self, temp_dir):
        """Test that to_dict handles Windows and Unix path separators."""
        # Unix-style path
        file = EbookFile(
            full_path=temp_dir / "subdir" / "book.pdf",
            relative_path=Path("subdir/book.pdf"),
            filename="book.pdf",
            file_size=100,
            file_extension=".pdf",
        )
        result = file.to_dict()
        # Path should be converted to string (OS-dependent)
        assert isinstance(result["relative_path"], str)

    def test_to_dict_preserves_field_values(self, sample_ebook_file):
        """Test that to_dict preserves all field values correctly."""
        result = sample_ebook_file.to_dict()
        assert result["filename"] == sample_ebook_file.filename
        assert result["file_size"] == sample_ebook_file.file_size
        assert result["relative_path"] == str(sample_ebook_file.relative_path)
        assert result["full_path"] == str(sample_ebook_file.full_path)

    def test_from_dict_creates_ebook_file(self, temp_dir):
        """Test that from_dict creates EbookFile from valid dictionary."""
        data = {
            "full_path": str(temp_dir / "test.pdf"),
            "relative_path": "test.pdf",
            "filename": "test.pdf",
            "file_size": "100",
        }
        file = EbookFile.from_dict(data, temp_dir)
        assert isinstance(file, EbookFile)
        assert file.filename == "test.pdf"
        assert file.file_size == 100
        assert file.file_extension == ".pdf"

    def test_from_dict_handles_missing_keys(self, temp_dir):
        """Test that from_dict handles missing keys (KeyError)."""
        data = {"filename": "test.pdf"}  # Missing required keys
        with pytest.raises(KeyError):
            EbookFile.from_dict(data, temp_dir)

    def test_from_dict_handles_invalid_file_size(self, temp_dir):
        """Test that from_dict handles invalid file_size (ValueError)."""
        data = {
            "full_path": str(temp_dir / "test.pdf"),
            "relative_path": "test.pdf",
            "filename": "test.pdf",
            "file_size": "not_a_number",
        }
        with pytest.raises(ValueError):
            EbookFile.from_dict(data, temp_dir)

    def test_from_dict_sets_file_extension(self, temp_dir):
        """Test that from_dict correctly sets file_extension from full_path."""
        data = {
            "full_path": str(temp_dir / "test.epub"),
            "relative_path": "test.epub",
            "filename": "test.epub",
            "file_size": "100",
        }
        file = EbookFile.from_dict(data, temp_dir)
        assert file.file_extension == ".epub"

    def test_from_dict_handles_relative_paths(self, temp_dir):
        """Test that from_dict handles relative paths correctly."""
        data = {
            "full_path": str(temp_dir / "subdir" / "book.pdf"),
            "relative_path": "subdir/book.pdf",
            "filename": "book.pdf",
            "file_size": "100",
        }
        file = EbookFile.from_dict(data, temp_dir)
        assert file.relative_path == Path("subdir/book.pdf")

    def test_from_dict_handles_absolute_paths(self, temp_dir):
        """Test that from_dict handles absolute paths correctly."""
        abs_path = temp_dir / "book.pdf"
        data = {
            "full_path": str(abs_path),
            "relative_path": "book.pdf",
            "filename": "book.pdf",
            "file_size": "100",
        }
        file = EbookFile.from_dict(data, temp_dir)
        assert file.full_path == abs_path

    def test_from_dict_handles_base_path_resolution(self, temp_dir):
        """Test that from_dict handles base_path resolution."""
        # base_path is used for context but full_path should be absolute
        data = {
            "full_path": str(temp_dir / "book.pdf"),
            "relative_path": "book.pdf",
            "filename": "book.pdf",
            "file_size": "100",
        }
        file = EbookFile.from_dict(data, temp_dir)
        assert file.full_path.is_absolute()
