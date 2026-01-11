"""
Tests for get_default_file_extensions function.
"""

from ebook_calibre_analyzer.utils import get_default_file_extensions


class TestGetDefaultFileExtensions:
    """Test cases for get_default_file_extensions function."""

    def test_returns_list_of_strings(self):
        """Test that get_default_file_extensions returns list of strings."""
        extensions = get_default_file_extensions()
        assert isinstance(extensions, list)
        assert all(isinstance(ext, str) for ext in extensions)

    def test_all_extensions_start_with_dot(self):
        """Test that get_default_file_extensions all extensions start with '.'."""
        extensions = get_default_file_extensions()
        assert all(
            ext.startswith(".") for ext in extensions
        ), "All extensions should start with '.'"

    def test_includes_pdf_cbr_cbz(self):
        """Test that get_default_file_extensions includes pdf, cbr, cbz."""
        extensions = get_default_file_extensions()
        assert ".pdf" in extensions
        assert ".cbr" in extensions
        assert ".cbz" in extensions

    def test_includes_ebook_formats(self):
        """Test that get_default_file_extensions includes epub, mobi, azw, azw3."""
        extensions = get_default_file_extensions()
        assert ".epub" in extensions
        assert ".mobi" in extensions
        assert ".azw" in extensions
        assert ".azw3" in extensions

    def test_returns_consistent_results(self):
        """Test that get_default_file_extensions returns consistent results (no randomness)."""
        result1 = get_default_file_extensions()
        result2 = get_default_file_extensions()
        assert result1 == result2, "Results should be consistent across calls"
