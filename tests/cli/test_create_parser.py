"""
Tests for create_parser function.
"""

import pytest

from ebook_calibre_analyzer.cli import create_parser


class TestCreateParser:
    """Test cases for create_parser function."""

    def test_creates_main_parser(self):
        """Test that create_parser creates main parser."""
        parser = create_parser()
        assert parser is not None
        assert parser.prog == "ebook-analyzer"

    def test_adds_subparsers(self):
        """Test that create_parser adds subparsers."""
        parser = create_parser()
        # Subparsers are added, command is required
        with pytest.raises(SystemExit):  # argparse exits on missing required arg
            parser.parse_args([])

    def test_includes_analyze_command(self):
        """Test that create_parser includes analyze command."""
        parser = create_parser()
        args = parser.parse_args(["analyze", "ebooks", "calibre"])
        assert args.command == "analyze"
        assert args.ebooks_folder is not None
        assert args.calibre_library_folder is not None

    def test_includes_copy_command(self):
        """Test that create_parser includes copy command."""
        parser = create_parser()
        args = parser.parse_args(["copy", "csv.csv", "ebooks", "target"])
        assert args.command == "copy"
        assert args.csv_file is not None
        assert args.ebooks_folder is not None
        assert args.target_folder is not None

    def test_sets_required_true_for_command(self):
        """Test that create_parser sets required=True for command."""
        parser = create_parser()
        # Should fail without command
        with pytest.raises(SystemExit):
            parser.parse_args([])
