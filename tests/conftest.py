"""
Shared pytest fixtures and configuration for all tests.
"""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from ebook_calibre_analyzer.models import EbookFile


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_ebook_file(temp_dir: Path) -> EbookFile:
    """Create a sample EbookFile for testing."""
    test_file = temp_dir / "test_book.pdf"
    test_file.write_bytes(b"test content")

    return EbookFile(
        full_path=test_file,
        relative_path=Path("test_book.pdf"),
        filename="test_book.pdf",
        file_size=len(b"test content"),
        file_extension=".pdf",
    )


@pytest.fixture
def sample_ebook_files(temp_dir: Path) -> list[EbookFile]:
    """Create multiple sample EbookFile objects for testing."""
    files = []
    for i in range(5):
        test_file = temp_dir / f"book_{i}.epub"
        content = f"content {i}".encode()
        test_file.write_bytes(content)

        files.append(
            EbookFile(
                full_path=test_file,
                relative_path=Path(f"book_{i}.epub"),
                filename=f"book_{i}.epub",
                file_size=len(content),
                file_extension=".epub",
            )
        )

    return files
