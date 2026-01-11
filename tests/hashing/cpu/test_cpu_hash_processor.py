"""
Tests for CPUHashProcessor class.
"""

import hashlib
from pathlib import Path

import pytest

from ebook_calibre_analyzer.hashing.cpu import CPUHashProcessor
from ebook_calibre_analyzer.models import EbookFile


class TestCPUHashProcessor:
    """Test cases for CPUHashProcessor class."""

    def test_init_sets_num_workers(self):
        """Test that __init__ initializes with provided num_workers."""
        processor = CPUHashProcessor(num_workers=5)
        assert processor.num_workers == 5

    def test_hash_first_1k_returns_hash(self, temp_dir):
        """Test that hash_first_1k returns hash of first 1KB."""
        test_file = temp_dir / "test.pdf"
        content = b"x" * 2048
        test_file.write_bytes(content)

        processor = CPUHashProcessor()
        file = EbookFile(
            full_path=test_file,
            relative_path=Path("test.pdf"),
            filename="test.pdf",
            file_size=len(content),
            file_extension=".pdf",
        )

        result = processor.hash_first_1k(file)
        assert isinstance(result, bytes)
        assert len(result) == 32
        expected = hashlib.sha256(content[:1024]).digest()
        assert result == expected

    def test_hash_full_file_returns_hash(self, temp_dir):
        """Test that hash_full_file returns hash of full file."""
        test_file = temp_dir / "test.pdf"
        content = b"test content" * 100
        test_file.write_bytes(content)

        processor = CPUHashProcessor()
        file = EbookFile(
            full_path=test_file,
            relative_path=Path("test.pdf"),
            filename="test.pdf",
            file_size=len(content),
            file_extension=".pdf",
        )

        result = processor.hash_full_file(file)
        assert isinstance(result, bytes)
        assert len(result) == 32
        expected = hashlib.sha256(content).digest()
        assert result == expected

    def test_hash_batch_returns_list_in_order(self, temp_dir):
        """Test that hash_batch returns list of hashes in same order as input."""
        processor = CPUHashProcessor()

        files = []
        contents = []
        for i in range(3):
            test_file = temp_dir / f"file{i}.pdf"
            content = f"content{i}".encode()
            test_file.write_bytes(content)
            contents.append(content)
            file = EbookFile(
                full_path=test_file,
                relative_path=Path(f"file{i}.pdf"),
                filename=f"file{i}.pdf",
                file_size=len(content),
                file_extension=".pdf",
            )
            files.append(file)

        results = processor.hash_batch(files, "full")
        assert len(results) == 3
        # Verify order matches
        for i, (_file, result) in enumerate(zip(files, results)):
            expected = hashlib.sha256(contents[i]).digest()
            assert result == expected

    def test_hash_batch_uses_correct_worker_for_1k(self, temp_dir):
        """Test that hash_batch uses correct worker for stage='1k'."""
        processor = CPUHashProcessor()

        test_file = temp_dir / "test.pdf"
        content = b"x" * 2048
        test_file.write_bytes(content)

        file = EbookFile(
            full_path=test_file,
            relative_path=Path("test.pdf"),
            filename="test.pdf",
            file_size=len(content),
            file_extension=".pdf",
        )

        results = processor.hash_batch([file], "1k")
        assert len(results) == 1
        expected = hashlib.sha256(content[:1024]).digest()
        assert results[0] == expected

    def test_hash_batch_uses_correct_worker_for_full(self, temp_dir):
        """Test that hash_batch uses correct worker for stage='full'."""
        processor = CPUHashProcessor()

        test_file = temp_dir / "test.pdf"
        content = b"test content" * 100
        test_file.write_bytes(content)

        file = EbookFile(
            full_path=test_file,
            relative_path=Path("test.pdf"),
            filename="test.pdf",
            file_size=len(content),
            file_extension=".pdf",
        )

        results = processor.hash_batch([file], "full")
        assert len(results) == 1
        expected = hashlib.sha256(content).digest()
        assert results[0] == expected

    def test_hash_batch_raises_value_error_for_unknown_stage(self, temp_dir):
        """Test that hash_batch raises ValueError for unknown stage."""
        processor = CPUHashProcessor()

        test_file = temp_dir / "test.pdf"
        test_file.write_bytes(b"content")

        file = EbookFile(
            full_path=test_file,
            relative_path=Path("test.pdf"),
            filename="test.pdf",
            file_size=len(b"content"),
            file_extension=".pdf",
        )

        with pytest.raises(ValueError):
            processor.hash_batch([file], "unknown")

    def test_hash_batch_handles_empty_files_list(self):
        """Test that hash_batch handles empty files list."""
        processor = CPUHashProcessor()
        results = processor.hash_batch([], "full")
        assert results == []

    def test_hash_batch_handles_exception_in_worker(self, temp_dir):
        """Test that hash_batch handles exceptions from worker processes."""
        processor = CPUHashProcessor()

        # Create a file that will cause an error
        test_file = temp_dir / "test.pdf"
        test_file.write_bytes(b"content")

        file = EbookFile(
            full_path=test_file,
            relative_path=Path("test.pdf"),
            filename="test.pdf",
            file_size=len(b"content"),
            file_extension=".pdf",
        )

        # Mock ProcessPoolExecutor to simulate exception
        from unittest.mock import MagicMock, patch

        # Create a proper mock Future that works with as_completed
        mock_future = MagicMock()
        mock_future.result.side_effect = Exception("Worker error")
        # Add attributes needed by as_completed
        mock_future._condition = MagicMock()
        mock_future._condition.acquire = MagicMock(return_value=True)
        mock_future._condition.release = MagicMock()
        mock_future._state = "FINISHED"

        with patch("ebook_calibre_analyzer.hashing.cpu.ProcessPoolExecutor") as mock_executor:
            mock_executor_instance = MagicMock()
            mock_executor.return_value.__enter__.return_value = mock_executor_instance
            mock_executor_instance.submit.return_value = mock_future
            mock_executor_instance.__enter__ = MagicMock(return_value=mock_executor_instance)
            mock_executor_instance.__exit__ = MagicMock(return_value=False)

            results = processor.hash_batch([file], "full")
            # Should return empty bytes on exception
            assert len(results) == 1
            assert results[0] == b""
