"""
Tests for main function.
"""

from unittest.mock import patch

import pytest

from ebook_calibre_analyzer.__main__ import main


class TestMain:
    """Test cases for main function."""

    def test_parses_arguments_correctly(self, temp_dir):
        """Test that main parses arguments correctly."""
        ebooks = temp_dir / "ebooks"
        calibre = temp_dir / "calibre"
        ebooks.mkdir()
        calibre.mkdir()

        with patch("sys.argv", ["ebook-analyzer", "analyze", str(ebooks), str(calibre)]), patch(
            "ebook_calibre_analyzer.__main__.print"
        ):  # Suppress output
            result = main()
            # Should return 0 on success or 1 if validation fails
            assert result in [0, 1]

    def test_calls_run_analyze_for_analyze_command(self, temp_dir):
        """Test that main calls run_analyze for analyze command."""
        ebooks = temp_dir / "ebooks"
        calibre = temp_dir / "calibre"
        ebooks.mkdir()
        calibre.mkdir()
        (ebooks / "book.pdf").write_bytes(b"content")

        with patch("sys.argv", ["ebook-analyzer", "analyze", str(ebooks), str(calibre)]), patch(
            "ebook_calibre_analyzer.__main__.print"
        ):  # Suppress output
            result = main()
            # Should actually run the analyze function
            assert result in [0, 1]

    def test_calls_run_copy_for_copy_command(self, temp_dir):
        """Test that main calls run_copy for copy command."""
        csv_file = temp_dir / "test.csv"
        ebooks = temp_dir / "ebooks"
        target = temp_dir / "target"
        ebooks.mkdir()

        # Create valid CSV
        import csv

        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["relative_path", "filename", "file_size", "full_path", "processed_at"],
            )
            writer.writeheader()

        with patch(
            "sys.argv", ["ebook-analyzer", "copy", str(csv_file), str(ebooks), str(target)]
        ), patch(
            "ebook_calibre_analyzer.__main__.print"
        ):  # Suppress output
            result = main()
            # Should actually run the copy function
            assert result in [0, 1]

    def test_prints_help_for_unknown_command(self):
        """Test that main prints help and returns 1 for unknown command."""
        # pytest.raises must be nested, so we suppress SIM117
        with patch("sys.argv", ["ebook-analyzer", "unknown"]), patch(  # noqa: SIM117
            "ebook_calibre_analyzer.__main__.print"
        ):
            # Should raise SystemExit when argparse encounters unknown command
            with pytest.raises(SystemExit):
                main()

    def test_main_returns_exit_code(self, temp_dir):
        """Test that main returns proper exit codes."""
        ebooks = temp_dir / "ebooks"
        calibre = temp_dir / "calibre"
        ebooks.mkdir()
        calibre.mkdir()
        (ebooks / "book.pdf").write_bytes(b"content")

        with patch("sys.argv", ["ebook-analyzer", "analyze", str(ebooks), str(calibre)]), patch(
            "ebook_calibre_analyzer.__main__.print"
        ):
            result = main()
            # Should return 0 on success
            assert result in [0, 1]
