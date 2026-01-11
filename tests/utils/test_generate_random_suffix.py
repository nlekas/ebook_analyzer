"""
Tests for generate_random_suffix function.
"""

import re

from ebook_calibre_analyzer.utils import WORD_LOOKUP_TABLE, generate_random_suffix


class TestGenerateRandomSuffix:
    """Test cases for generate_random_suffix function."""

    def test_returns_string_in_correct_format(self):
        """Test that generate_random_suffix returns string in format wordNN (e.g., 'eagle73')."""
        suffix = generate_random_suffix()
        # Format: word + 2-digit number
        pattern = r"^[a-z]+[0-9]{2}$"
        assert re.match(pattern, suffix), f"Suffix '{suffix}' doesn't match expected format"

    def test_returns_word_from_lookup_table(self):
        """Test that generate_random_suffix returns word from WORD_LOOKUP_TABLE."""
        # Generate many suffixes to increase chance of seeing all words
        suffixes = [generate_random_suffix() for _ in range(1000)]
        words = [s[:-2] for s in suffixes]  # Remove 2-digit number
        # At least one word should be from lookup table
        assert any(word in WORD_LOOKUP_TABLE for word in words)

    def test_returns_number_between_00_99(self):
        """Test that generate_random_suffix returns number between 00-99 (2 digits)."""
        suffixes = [generate_random_suffix() for _ in range(100)]
        for suffix in suffixes:
            number_str = suffix[-2:]  # Last 2 characters
            number = int(number_str)
            assert 0 <= number <= 99, f"Number {number} not in range 0-99"
            assert len(number_str) == 2, f"Number '{number_str}' is not 2 digits"

    def test_returns_different_values_on_multiple_calls(self):
        """Test that generate_random_suffix returns different values on multiple calls (randomness)."""
        suffixes = [generate_random_suffix() for _ in range(100)]
        # With 100 calls, we should get some variety (not all the same)
        unique_suffixes = set(suffixes)
        assert len(unique_suffixes) > 1, "All suffixes were identical (no randomness)"

    def test_number_is_zero_padded(self):
        """Test that generate_random_suffix number is zero-padded (e.g., '05' not '5')."""
        # Generate many to catch a single-digit number
        for _ in range(1000):
            suffix = generate_random_suffix()
            number_str = suffix[-2:]
            number = int(number_str)
            if number < 10:
                assert number_str.startswith(
                    "0"
                ), f"Number {number} should be zero-padded: '{number_str}'"
        # It's possible we don't get a single-digit number, but if we do, it should be padded
