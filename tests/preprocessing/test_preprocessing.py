"""
Tests for preprocess_files function.
"""

from pathlib import Path

from ebook_calibre_analyzer.models import EbookFile
from ebook_calibre_analyzer.preprocessing import preprocess_files


class TestPreprocessFiles:
    """Test cases for preprocess_files function."""

    def test_returns_empty_dict_when_files_empty(self):
        """Test that preprocess_files returns empty dicts when files list is empty."""
        result = preprocess_files([])
        assert result == {"gpu": [], "cpu": [], "skip": []}

    def test_categorizes_to_gpu_when_available_and_above_threshold(self, temp_dir):
        """Test that preprocess_files categorizes files to GPU when gpu_available=True and size >= threshold."""
        threshold = 100 * 1024 * 1024  # 100MB
        large_file = EbookFile(
            full_path=temp_dir / "large.pdf",
            relative_path=Path("large.pdf"),
            filename="large.pdf",
            file_size=threshold,
            file_extension=".pdf",
        )
        result = preprocess_files([large_file], gpu_available=True, gpu_threshold=threshold)
        assert large_file in result["gpu"]
        assert large_file.processing_method == "gpu"

    def test_categorizes_to_cpu_when_below_threshold(self, temp_dir):
        """Test that preprocess_files categorizes files to CPU when size < threshold."""
        threshold = 100 * 1024 * 1024  # 100MB
        small_file = EbookFile(
            full_path=temp_dir / "small.pdf",
            relative_path=Path("small.pdf"),
            filename="small.pdf",
            file_size=threshold - 1,
            file_extension=".pdf",
        )
        result = preprocess_files([small_file], gpu_available=True, gpu_threshold=threshold)
        assert small_file in result["cpu"]
        assert small_file.processing_method == "cpu"

    def test_categorizes_to_cpu_when_gpu_not_available(self, temp_dir):
        """Test that preprocess_files categorizes files to CPU when gpu_available=False."""
        large_file = EbookFile(
            full_path=temp_dir / "large.pdf",
            relative_path=Path("large.pdf"),
            filename="large.pdf",
            file_size=200 * 1024 * 1024,  # 200MB
            file_extension=".pdf",
        )
        result = preprocess_files([large_file], gpu_available=False)
        assert large_file in result["cpu"]
        assert large_file.processing_method == "cpu"

    def test_skips_files_in_processed_files(self, temp_dir):
        """Test that preprocess_files skips files in processed_files set."""
        file = EbookFile(
            full_path=temp_dir / "test.pdf",
            relative_path=Path("test.pdf"),
            filename="test.pdf",
            file_size=100,
            file_extension=".pdf",
        )
        processed_files = {str(file.full_path)}
        result = preprocess_files([file], processed_files=processed_files)
        assert file in result["skip"]
        assert file not in result["cpu"]
        assert file not in result["gpu"]

    def test_sets_processing_method_correctly(self, temp_dir):
        """Test that preprocess_files sets processing_method correctly on files."""
        threshold = 100 * 1024 * 1024
        gpu_file = EbookFile(
            full_path=temp_dir / "gpu.pdf",
            relative_path=Path("gpu.pdf"),
            filename="gpu.pdf",
            file_size=threshold,
            file_extension=".pdf",
        )
        cpu_file = EbookFile(
            full_path=temp_dir / "cpu.pdf",
            relative_path=Path("cpu.pdf"),
            filename="cpu.pdf",
            file_size=threshold - 1,
            file_extension=".pdf",
        )
        preprocess_files([gpu_file, cpu_file], gpu_available=True, gpu_threshold=threshold)
        assert gpu_file.processing_method == "gpu"
        assert cpu_file.processing_method == "cpu"
