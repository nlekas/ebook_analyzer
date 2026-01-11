"""
Tests for create_copy_parser function.
"""

import argparse

from ebook_calibre_analyzer.cli import create_copy_parser


class TestCreateCopyParser:
    """Test cases for create_copy_parser function."""

    def test_creates_parser_with_correct_name(self):
        """Test that create_copy_parser creates parser with correct name."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        copy_parser = create_copy_parser(subparsers)
        assert copy_parser is not None

    def test_adds_required_positional_arguments(self):
        """Test that create_copy_parser adds required positional arguments."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        copy_parser = create_copy_parser(subparsers)

        args = copy_parser.parse_args(["csv.csv", "ebooks", "target"])
        assert args.csv_file is not None
        assert args.ebooks_folder is not None
        assert args.target_folder is not None

    def test_adds_all_optional_arguments(self):
        """Test that create_copy_parser adds all optional arguments."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        copy_parser = create_copy_parser(subparsers)

        args = copy_parser.parse_args(
            [
                "csv.csv",
                "ebooks",
                "target",
                "--conflict-handling",
                "skip",
                "--dry-run",
                "--workers",
                "8",
            ]
        )
        assert args.conflict_handling == "skip"
        assert args.dry_run is True
        assert args.workers == 8
