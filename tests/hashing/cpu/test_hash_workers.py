"""
Tests for CPU hash worker functions.
"""

import hashlib

from ebook_calibre_analyzer.hashing.cpu import _hash_first_1k_worker, _hash_full_file_worker


class TestHashFirst1KWorker:
    """Test cases for _hash_first_1k_worker function."""

    def test_returns_hash_of_first_1024_bytes(self, temp_dir):
        """Test that _hash_first_1k_worker returns hash of first 1024 bytes."""
        test_file = temp_dir / "test.pdf"
        content = b"x" * 2048  # 2KB file
        test_file.write_bytes(content)

        result = _hash_first_1k_worker(str(test_file))
        assert isinstance(result, bytes)
        assert len(result) == 32  # SHA256 digest length

        # Verify it's hashing only first 1KB
        expected_hash = hashlib.sha256(content[:1024]).digest()
        assert result == expected_hash

    def test_returns_empty_bytes_on_error(self):
        """Test that _hash_first_1k_worker returns empty bytes on file error."""
        result = _hash_first_1k_worker("/nonexistent/file.pdf")
        assert result == b""

    def test_returns_consistent_hash(self, temp_dir):
        """Test that _hash_first_1k_worker returns consistent hash for same file."""
        test_file = temp_dir / "test.pdf"
        content = b"test content" * 100
        test_file.write_bytes(content)

        hash1 = _hash_first_1k_worker(str(test_file))
        hash2 = _hash_first_1k_worker(str(test_file))
        assert hash1 == hash2

    def test_handles_files_smaller_than_1kb(self, temp_dir):
        """Test that _hash_first_1k_worker handles files smaller than 1KB."""
        test_file = temp_dir / "small.pdf"
        content = b"small"
        test_file.write_bytes(content)

        result = _hash_first_1k_worker(str(test_file))
        assert isinstance(result, bytes)
        assert len(result) == 32
        # Should hash whatever is available
        expected_hash = hashlib.sha256(content).digest()
        assert result == expected_hash

    def test_handles_files_exactly_1kb(self, temp_dir):
        """Test that _hash_first_1k_worker handles files exactly 1KB."""
        test_file = temp_dir / "exact1k.pdf"
        content = b"x" * 1024
        test_file.write_bytes(content)

        result = _hash_first_1k_worker(str(test_file))
        assert isinstance(result, bytes)
        assert len(result) == 32
        expected_hash = hashlib.sha256(content).digest()
        assert result == expected_hash


class TestHashFullFileWorker:
    """Test cases for _hash_full_file_worker function."""

    def test_returns_hash_of_entire_file(self, temp_dir):
        """Test that _hash_full_file_worker returns hash of entire file."""
        test_file = temp_dir / "test.pdf"
        content = b"test content" * 1000
        test_file.write_bytes(content)

        result = _hash_full_file_worker(str(test_file))
        assert isinstance(result, bytes)
        assert len(result) == 32  # SHA256 digest length

        expected_hash = hashlib.sha256(content).digest()
        assert result == expected_hash

    def test_returns_empty_bytes_on_error(self):
        """Test that _hash_full_file_worker returns empty bytes on file error."""
        result = _hash_full_file_worker("/nonexistent/file.pdf")
        assert result == b""

    def test_returns_consistent_hash(self, temp_dir):
        """Test that _hash_full_file_worker returns consistent hash for same file."""
        test_file = temp_dir / "test.pdf"
        content = b"test content" * 1000
        test_file.write_bytes(content)

        hash1 = _hash_full_file_worker(str(test_file))
        hash2 = _hash_full_file_worker(str(test_file))
        assert hash1 == hash2

    def test_handles_empty_file(self, temp_dir):
        """Test that _hash_full_file_worker handles empty file."""
        test_file = temp_dir / "empty.pdf"
        test_file.write_bytes(b"")

        result = _hash_full_file_worker(str(test_file))
        assert isinstance(result, bytes)
        assert len(result) == 32
        expected_hash = hashlib.sha256(b"").digest()
        assert result == expected_hash

    def test_reads_in_1mb_chunks(self, temp_dir):
        """Test that _hash_full_file_worker reads in 1MB chunks."""
        # Create a file larger than 1MB to test chunking
        test_file = temp_dir / "large.pdf"
        content = b"x" * (2 * 1024 * 1024)  # 2MB
        test_file.write_bytes(content)

        result = _hash_full_file_worker(str(test_file))
        assert isinstance(result, bytes)
        assert len(result) == 32
        # Verify it hashed the entire file correctly
        expected_hash = hashlib.sha256(content).digest()
        assert result == expected_hash
