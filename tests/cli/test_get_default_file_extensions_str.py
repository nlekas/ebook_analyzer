"""
Tests for get_default_file_extensions_str function.
"""

from ebook_calibre_analyzer.cli import get_default_file_extensions_str


class TestGetDefaultFileExtensionsStr:
    """Test cases for get_default_file_extensions_str function."""

    def test_returns_comma_separated_string(self):
        """Test that get_default_file_extensions_str returns comma-separated string."""
        result = get_default_file_extensions_str()
        assert isinstance(result, str)
        assert "," in result

    def test_removes_leading_dots(self):
        """Test that get_default_file_extensions_str removes leading dots from extensions."""
        result = get_default_file_extensions_str()
        # All extensions in the string should not start with dot
        extensions = [ext.strip() for ext in result.split(",")]
        assert all(
            not ext.startswith(".") for ext in extensions
        ), "Extensions should not have leading dots"

    def test_includes_all_default_extensions(self):
        """Test that get_default_file_extensions_str includes all default extensions."""
        from ebook_calibre_analyzer.utils import get_default_file_extensions

        result = get_default_file_extensions_str()
        default_exts = get_default_file_extensions()
        # Check that all default extensions (without dots) are in the string
        for ext in default_exts:
            ext_without_dot = ext.replace(".", "")
            assert ext_without_dot in result, f"Extension '{ext_without_dot}' not found in result"
