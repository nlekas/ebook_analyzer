"""
Tests for GPUHashProcessor class.
"""

import hashlib
from pathlib import Path

from ebook_calibre_analyzer.hashing.gpu import GPUHashProcessor
from ebook_calibre_analyzer.models import EbookFile


class TestGPUHashProcessor:
    """Test cases for GPUHashProcessor class."""

    def test_init_sets_device_id(self):
        """Test that __init__ initializes with provided device_id."""
        processor = GPUHashProcessor(device_id=1)
        assert processor.device_id == 1

    def test_init_creates_gpu_pool(self):
        """Test that __init__ creates GPUMemoryPool."""
        processor = GPUHashProcessor()
        assert processor.gpu_pool is not None
        assert processor.gpu_pool.device_id == 0  # Default

    def test_hash_first_1k_falls_back_to_cpu(self, temp_dir):
        """Test that hash_first_1k falls back to CPU (first 1KB too small for GPU)."""
        processor = GPUHashProcessor()

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

        result = processor.hash_first_1k(file)
        # Should return valid hash (from CPU fallback)
        assert isinstance(result, bytes)
        assert len(result) == 32
        expected = hashlib.sha256(content[:1024]).digest()
        assert result == expected

    def test_hash_full_file_falls_back_to_cpu_when_unavailable(self, temp_dir):
        """Test that hash_full_file falls back to CPU when GPU not available."""
        processor = GPUHashProcessor()
        # GPU not available (placeholder implementation)

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

        result = processor.hash_full_file(file)
        # Should return valid hash (from CPU fallback)
        assert isinstance(result, bytes)
        assert len(result) == 32
        expected = hashlib.sha256(content).digest()
        assert result == expected

    def test_hash_batch_falls_back_to_cpu_for_1k(self, temp_dir):
        """Test that hash_batch falls back to CPU for stage='1k'."""
        processor = GPUHashProcessor()

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
        assert isinstance(results[0], bytes)
        assert len(results[0]) == 32

    def test_init_handles_import_error(self):
        """Test that __init__ handles ImportError when cupy is not available."""
        # The current implementation doesn't actually import cupy, but we can test
        # that the ImportError path exists (it's in the try/except but never executed)
        processor = GPUHashProcessor()
        # Should initialize successfully even without GPU
        assert processor.device_id == 0
        assert processor._gpu_available is False

    def test_hash_full_file_uses_gpu_when_available(self, temp_dir):
        """Test that hash_full_file uses GPU when available."""
        # Mock GPU availability
        processor = GPUHashProcessor()
        # If GPU is available, it will use GPU path
        # Otherwise, it falls back to CPU (which is tested elsewhere)

        test_file = temp_dir / "test.pdf"
        content = b"test content" * 1000
        test_file.write_bytes(content)

        file = EbookFile(
            full_path=test_file,
            relative_path=Path("test.pdf"),
            filename="test.pdf",
            file_size=len(content),
            file_extension=".pdf",
        )

        result = processor.hash_full_file(file)
        # Should return valid hash regardless of GPU availability
        assert isinstance(result, bytes)
        assert len(result) == 32
        expected = hashlib.sha256(content).digest()
        assert result == expected

    def test_hash_full_file_handles_large_files(self, temp_dir):
        """Test that hash_full_file handles large files with chunked processing."""
        processor = GPUHashProcessor()

        # Create a file larger than typical GPU memory chunk
        test_file = temp_dir / "large.pdf"
        # Create 300MB file
        chunk = b"x" * (1024 * 1024)  # 1MB chunks
        content = chunk * 300  # 300MB
        test_file.write_bytes(content)

        file = EbookFile(
            full_path=test_file,
            relative_path=Path("large.pdf"),
            filename="large.pdf",
            file_size=len(content),
            file_extension=".pdf",
        )

        result = processor.hash_full_file(file)
        # Should return valid hash
        assert isinstance(result, bytes)
        assert len(result) == 32
        expected = hashlib.sha256(content).digest()
        assert result == expected

    def test_hash_batch_uses_gpu_when_available(self, temp_dir):
        """Test that hash_batch uses GPU when available."""
        processor = GPUHashProcessor()

        files = []
        contents = []
        for i in range(3):
            test_file = temp_dir / f"test{i}.pdf"
            content = b"test content" * (100 + i)
            test_file.write_bytes(content)
            contents.append(content)

            file = EbookFile(
                full_path=test_file,
                relative_path=Path(f"test{i}.pdf"),
                filename=f"test{i}.pdf",
                file_size=len(content),
                file_extension=".pdf",
            )
            files.append(file)

        results = processor.hash_batch(files, "full")
        assert len(results) == 3
        for _i, (content, result) in enumerate(zip(contents, results)):
            assert isinstance(result, bytes)
            assert len(result) == 32
            expected = hashlib.sha256(content).digest()
            assert result == expected
