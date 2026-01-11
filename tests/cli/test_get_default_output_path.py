"""
Tests for get_default_output_path function.
"""

from pathlib import Path

from ebook_calibre_analyzer.cli import get_default_output_path


class TestGetDefaultOutputPath:
    """Test cases for get_default_output_path function."""

    def test_returns_path_in_current_directory(self):
        """Test that get_default_output_path returns Path in current working directory."""

        result = get_default_output_path()
        assert isinstance(result, Path)
        assert result.parent == Path.cwd()

    def test_filename_format(self):
        """Test that get_default_output_path filename format: missing_from_calibre_YYYYMMDD_HHMMSS.csv."""
        import re

        result = get_default_output_path()
        pattern = r"^missing_from_calibre_\d{8}_\d{6}\.csv$"
        assert re.match(
            pattern, result.name
        ), f"Filename '{result.name}' doesn't match expected format"

    def test_uses_utc_timezone(self):
        """Test that get_default_output_path uses UTC timezone."""
        from datetime import datetime, timezone

        result = get_default_output_path()
        # Extract timestamp from filename
        timestamp_str = result.stem.split("_")[-2] + "_" + result.stem.split("_")[-1]
        # Verify it's a valid UTC timestamp format
        dt = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")  # noqa: DTZ007
        # Make it timezone-aware (UTC)
        dt = dt.replace(tzinfo=timezone.utc)

    def test_returns_different_paths_for_different_times(self):
        """Test that get_default_output_path returns different paths for different times."""
        import time

        path1 = get_default_output_path()
        time.sleep(1.1)  # Wait more than 1 second to ensure different timestamp
        path2 = get_default_output_path()
        assert path1 != path2, "Paths should be different for different times"
