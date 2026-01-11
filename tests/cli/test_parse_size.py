"""
Tests for parse_size function.
"""

import pytest

from ebook_calibre_analyzer.cli import parse_size


class TestParseSize:
    """Test cases for parse_size function."""

    def test_parses_kb_suffix(self):
        """Test that parse_size parses KB suffix (case-insensitive)."""
        assert parse_size("100KB") == 100 * 1024
        assert parse_size("100kb") == 100 * 1024
        assert parse_size("100Kb") == 100 * 1024
        assert parse_size("1KB") == 1024

    def test_parses_mb_suffix(self):
        """Test that parse_size parses MB suffix."""
        assert parse_size("100MB") == 100 * 1024**2
        assert parse_size("1MB") == 1024**2

    def test_parses_gb_suffix(self):
        """Test that parse_size parses GB suffix."""
        assert parse_size("100GB") == 100 * 1024**3
        assert parse_size("1GB") == 1024**3

    def test_parses_tb_suffix(self):
        """Test that parse_size parses TB suffix."""
        assert parse_size("100TB") == 100 * 1024**4
        assert parse_size("1TB") == 1024**4

    def test_parses_plain_number(self):
        """Test that parse_size parses plain number (assumes bytes)."""
        assert parse_size("1024") == 1024
        assert parse_size("0") == 0
        assert parse_size("500000000000") == 500_000_000_000

    def test_handles_decimal_numbers(self):
        """Test that parse_size handles decimal numbers."""
        assert parse_size("1.5MB") == int(1.5 * 1024**2)
        assert parse_size("2.5GB") == int(2.5 * 1024**3)
        assert parse_size("0.5KB") == int(0.5 * 1024)

    def test_raises_value_error_for_invalid_format(self):
        """Test that parse_size raises ValueError for invalid format."""
        with pytest.raises(ValueError):
            parse_size("invalid")
        with pytest.raises(ValueError):
            parse_size("100XX")
        with pytest.raises(ValueError):
            parse_size("abc")

    def test_handles_whitespace(self):
        """Test that parse_size handles whitespace."""
        assert parse_size(" 100KB ") == 100 * 1024
        assert parse_size("100 MB") == 100 * 1024**2
        assert parse_size(" 100GB ") == 100 * 1024**3

    def test_calculates_correct_byte_values(self):
        """Test that parse_size calculates correct byte values."""
        assert parse_size("1KB") == 1024
        assert parse_size("1MB") == 1024**2
        assert parse_size("1GB") == 1024**3
        assert parse_size("1TB") == 1024**4
        assert parse_size("100MB") == 100 * 1024**2
