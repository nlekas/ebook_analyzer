"""
Tests for create_analyze_parser function.
"""

import argparse

from ebook_calibre_analyzer.cli import create_analyze_parser


class TestCreateAnalyzeParser:
    """Test cases for create_analyze_parser function."""

    def test_creates_parser_with_correct_name(self):
        """Test that create_analyze_parser creates parser with correct name."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        analyze_parser = create_analyze_parser(subparsers)
        assert analyze_parser is not None

    def test_adds_required_positional_arguments(self):
        """Test that create_analyze_parser adds required positional arguments."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        analyze_parser = create_analyze_parser(subparsers)

        # Test that positional args exist
        args = analyze_parser.parse_args(["ebooks", "calibre"])
        assert args.ebooks_folder is not None
        assert args.calibre_library_folder is not None

    def test_adds_all_optional_arguments(self):
        """Test that create_analyze_parser adds all optional arguments."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        analyze_parser = create_analyze_parser(subparsers)

        # Test optional args exist
        args = analyze_parser.parse_args(
            [
                "ebooks",
                "calibre",
                "--output",
                "output.csv",
                "--file-types",
                "pdf",
                "epub",
                "--resume",
                "resume.csv",
                "--use-gpu",
                "--gpu-device",
                "1",
                "--gpu-threshold",
                "200MB",
                "--batch-size",
                "50",
                "--workers",
                "5",
            ]
        )
        assert args.output is not None
        assert args.file_types is not None
        assert args.resume is not None
        assert args.use_gpu is True
        assert args.gpu_device == 1
        assert args.gpu_threshold == "200MB"
        assert args.batch_size == 50
        assert args.workers == 5

    def test_sets_correct_defaults(self):
        """Test that create_analyze_parser sets correct defaults."""
        parser = argparse.ArgumentParser()
        subparsers = parser.add_subparsers()
        analyze_parser = create_analyze_parser(subparsers)

        args = analyze_parser.parse_args(["ebooks", "calibre"])
        assert args.output is None
        assert args.file_types is None
        assert args.resume is None
        assert args.use_gpu is False
        assert args.gpu_device == 0
        assert args.gpu_threshold == "100MB"
        assert args.batch_size == 100
        assert args.workers == 10
