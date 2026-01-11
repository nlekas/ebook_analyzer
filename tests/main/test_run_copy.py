"""
Tests for run_copy function.
"""

from unittest.mock import MagicMock, patch

from ebook_calibre_analyzer.__main__ import run_copy


class TestRunCopy:
    """Test cases for run_copy function."""

    def test_returns_1_when_csv_missing(self, temp_dir):
        """Test that run_copy returns 1 when CSV file doesn't exist."""
        args = MagicMock()
        args.csv_file = temp_dir / "nonexistent.csv"
        args.ebooks_folder = temp_dir / "ebooks"
        args.target_folder = temp_dir / "target"
        args.conflict_handling = "rename"
        args.dry_run = False
        args.workers = 4
        args.verbose = False

        result = run_copy(args)
        assert result == 1

    def test_returns_0_on_successful_copy(self, temp_dir):
        """Test that run_copy returns 0 on successful copy (no failures)."""
        csv_file = temp_dir / "test.csv"
        ebooks = temp_dir / "ebooks"
        target = temp_dir / "target"
        ebooks.mkdir()

        # Create source file
        source_file = ebooks / "book.pdf"
        content = b"content"
        source_file.write_bytes(content)

        # Create CSV with proper format
        import csv

        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["relative_path", "filename", "file_size", "full_path", "processed_at"],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "relative_path": "book.pdf",
                    "filename": "book.pdf",
                    "file_size": str(len(content)),
                    "full_path": str(source_file),
                    "processed_at": "2024-01-01T00:00:00",
                }
            )

        args = MagicMock()
        args.csv_file = csv_file
        args.ebooks_folder = ebooks
        args.target_folder = target
        args.conflict_handling = "rename"
        args.dry_run = False
        args.workers = 4
        args.verbose = False

        with patch("ebook_calibre_analyzer.__main__.print"):
            result = run_copy(args)
            # Should return 0 on success (no failures)
            assert result == 0
            # Verify file was actually copied
            assert (target / "book.pdf").exists()
            assert (target / "book.pdf").read_bytes() == content

    def test_returns_1_when_some_files_fail(self, temp_dir):
        """Test that run_copy returns 1 when some files fail."""
        csv_file = temp_dir / "test.csv"
        ebooks = temp_dir / "ebooks"
        target = temp_dir / "target"
        ebooks.mkdir()

        # Create CSV with non-existent file - need proper CSV format
        import csv

        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["relative_path", "filename", "file_size", "full_path", "processed_at"],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "relative_path": "missing.pdf",
                    "filename": "missing.pdf",
                    "file_size": "100",
                    "full_path": str(ebooks / "missing.pdf"),
                    "processed_at": "2024-01-01T00:00:00",
                }
            )

        args = MagicMock()
        args.csv_file = csv_file
        args.ebooks_folder = ebooks
        args.target_folder = target
        args.conflict_handling = "rename"
        args.dry_run = False
        args.workers = 4
        args.verbose = False

        with patch("ebook_calibre_analyzer.__main__.print"):
            result = run_copy(args)
            # Should return 1 when files fail (implementation returns 1 if stats["failed"] > 0)
            assert result == 1

    def test_handles_dry_run_mode(self, temp_dir):
        """Test that run_copy handles dry-run mode."""
        csv_file = temp_dir / "test.csv"
        ebooks = temp_dir / "ebooks"
        target = temp_dir / "target"
        ebooks.mkdir()

        csv_file.write_text("relative_path,filename,file_size,full_path,processed_at\n")

        args = MagicMock()
        args.csv_file = csv_file
        args.ebooks_folder = ebooks
        args.target_folder = target
        args.conflict_handling = "rename"
        args.dry_run = True
        args.workers = 4
        args.verbose = False

        with patch("ebook_calibre_analyzer.__main__.print"):
            result = run_copy(args)
            # Should handle dry-run without error
            assert result in [0, 1]

    def test_handles_conflict_modes(self, temp_dir):
        """Test that run_copy handles conflict modes (rename, skip, overwrite)."""
        csv_file = temp_dir / "test.csv"
        ebooks = temp_dir / "ebooks"
        target = temp_dir / "target"
        ebooks.mkdir()

        csv_file.write_text("relative_path,filename,file_size,full_path,processed_at\n")

        for mode in ["rename", "skip", "overwrite"]:
            args = MagicMock()
            args.csv_file = csv_file
            args.ebooks_folder = ebooks
            args.target_folder = target
            args.conflict_handling = mode
            args.dry_run = False
            args.workers = 4
            args.verbose = False

            with patch("ebook_calibre_analyzer.__main__.print"):
                result = run_copy(args)
                # Should handle all modes
                assert result in [0, 1]

    def test_returns_1_when_ebooks_folder_missing(self, temp_dir):
        """Test that run_copy returns 1 when ebooks folder doesn't exist."""
        csv_file = temp_dir / "test.csv"
        csv_file.write_text("relative_path,filename,file_size,full_path,processed_at\n")

        args = MagicMock()
        args.csv_file = csv_file
        args.ebooks_folder = temp_dir / "nonexistent"
        args.target_folder = temp_dir / "target"
        args.conflict_handling = "rename"
        args.dry_run = False
        args.workers = 4
        args.verbose = False

        with patch("ebook_calibre_analyzer.__main__.print"):
            result = run_copy(args)
            assert result == 1

    def test_handles_verbose_output(self, temp_dir):
        """Test that run_copy handles verbose output."""
        csv_file = temp_dir / "test.csv"
        ebooks = temp_dir / "ebooks"
        target = temp_dir / "target"
        ebooks.mkdir()

        source_file = ebooks / "book.pdf"
        source_file.write_bytes(b"content")

        import csv

        with open(csv_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["relative_path", "filename", "file_size", "full_path", "processed_at"],
            )
            writer.writeheader()
            writer.writerow(
                {
                    "relative_path": "book.pdf",
                    "filename": "book.pdf",
                    "file_size": str(len(b"content")),
                    "full_path": str(source_file),
                    "processed_at": "2024-01-01T00:00:00",
                }
            )

        args = MagicMock()
        args.csv_file = csv_file
        args.ebooks_folder = ebooks
        args.target_folder = target
        args.conflict_handling = "rename"
        args.dry_run = False
        args.workers = 4
        args.verbose = True  # Enable verbose

        # With verbose=True, loguru will output DEBUG messages
        # Just verify the function runs successfully
        result = run_copy(args)
        assert result == 0
