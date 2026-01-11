"""
Recursive file discovery module for finding ebook files in nested directory structures.
"""

from pathlib import Path
from typing import List, Set

from .models import EbookFile
from .utils import get_default_file_extensions


def discover_files_recursive(
    base_path: Path, file_extensions: List[str] = None, exclude_paths: Set[Path] = None
) -> List[EbookFile]:
    """
    Recursively discover all files matching extensions in base_path and all subdirectories.

    Args:
        base_path: Root directory to search (ebooks or calibre library)
        file_extensions: List of file extensions to match (case-insensitive).
                        If None, uses default extensions.
        exclude_paths: Set of paths to exclude from discovery (for resume mode)

    Returns:
        List of EbookFile objects with full_path and relative_path set
    """
    if file_extensions is None:
        file_extensions = get_default_file_extensions()

    if exclude_paths is None:
        exclude_paths = set()

    files = []
    base_path = Path(base_path).resolve()

    if not base_path.exists():
        raise FileNotFoundError(f"Base path does not exist: {base_path}")

    if not base_path.is_dir():
        raise NotADirectoryError(f"Base path is not a directory: {base_path}")

    # Normalize extensions (ensure they start with . and are lowercase)
    normalized_extensions = set()
    for ext in file_extensions:
        ext = ext.lower()
        if not ext.startswith("."):
            ext = "." + ext
        normalized_extensions.add(ext)

    # Recursively find all matching files
    for ext in normalized_extensions:
        pattern = f"*{ext}"
        try:
            for file_path in base_path.rglob(pattern):
                if file_path.is_file():
                    # Skip if in exclude_paths (for resume mode)
                    if file_path in exclude_paths:
                        continue

                    try:
                        relative_path = file_path.relative_to(base_path)
                        file_size = file_path.stat().st_size

                        files.append(
                            EbookFile(
                                full_path=file_path,
                                relative_path=relative_path,
                                filename=file_path.name,
                                file_size=file_size,
                                file_extension=ext,
                            )
                        )
                    except (OSError, ValueError):
                        # Skip files we can't access or process
                        # (permissions, symlinks, etc.)
                        continue
        except (OSError, PermissionError):
            # Skip directories we can't access
            continue

    return files
