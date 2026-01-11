"""
File copying module with flat structure and conflict resolution.
"""

import shutil
from pathlib import Path
from typing import Dict, List

from .models import EbookFile
from .utils import generate_random_suffix


class FileCopier:
    """
    Handles copying files from CSV to target.

    Always flattens to target root - all files copied directly to the root
    of the target folder, regardless of their original directory structure.
    """

    def __init__(
        self,
        csv_path: Path,
        source_base: Path,
        target_folder: Path,
        conflict_handling: str = "rename",
        num_workers: int = 4,
    ):
        """
        Initialize file copier.

        Args:
            csv_path: Path to CSV file with files to copy
            source_base: Base path of source files (ebooks folder)
            target_folder: Target folder (Calibre import folder)
            conflict_handling: How to handle conflicts: 'rename', 'skip', 'overwrite'
            num_workers: Number of parallel copy workers
        """
        self.csv_path = Path(csv_path)
        self.source_base = Path(source_base)
        self.target_folder = Path(target_folder)
        self.conflict_handling = conflict_handling
        self.num_workers = num_workers

        if conflict_handling not in ["rename", "skip", "overwrite"]:
            raise ValueError(f"Invalid conflict_handling: {conflict_handling}")

    def load_files_from_csv(self) -> List[EbookFile]:
        """
        Load files from CSV.

        Returns:
            List of EbookFile objects
        """
        from .csv_handler import CSVHandler

        handler = CSVHandler(self.csv_path, resume_mode=False)
        return handler.read_all(self.source_base)

    def _resolve_filename_conflict(self, filename: str, target: Path) -> Path:
        """
        Resolve filename conflict by generating new name.

        Args:
            filename: Original filename
            target: Target path that already exists

        Returns:
            New path with resolved filename
        """
        # Generate new name: filename_randomwordNN.ext
        stem = target.stem
        suffix = target.suffix

        # Try up to 100 times to find a unique name
        for _ in range(100):
            random_suffix = generate_random_suffix()
            new_name = f"{stem}_{random_suffix}{suffix}"
            new_path = target.parent / new_name

            if not new_path.exists():
                return new_path

        # If we can't find a unique name, append a counter
        counter = 1
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = target.parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1

    def copy_file(self, file: EbookFile, dry_run: bool = False) -> Dict[str, any]:
        """
        Copy a single file to target folder.

        Args:
            file: EbookFile to copy
            dry_run: If True, don't actually copy, just return what would be done

        Returns:
            Dictionary with 'success', 'source', 'target', 'message' keys
        """
        # Validate source file exists
        if not file.full_path.exists():
            return {
                "success": False,
                "source": str(file.full_path),
                "target": None,
                "message": f"Source file does not exist: {file.full_path}",
            }

        # Target is always flat: target_folder / filename
        target_path = self.target_folder / file.filename

        # Handle conflicts
        if target_path.exists():
            if self.conflict_handling == "skip":
                return {
                    "success": False,
                    "source": str(file.full_path),
                    "target": str(target_path),
                    "message": f"Target file exists, skipping: {target_path}",
                }
            elif self.conflict_handling == "rename":
                target_path = self._resolve_filename_conflict(file.filename, target_path)
            elif self.conflict_handling == "overwrite":
                # Will overwrite, no change needed
                pass

        if dry_run:
            return {
                "success": True,
                "source": str(file.full_path),
                "target": str(target_path),
                "message": f"Would copy to: {target_path}",
            }

        # Ensure target directory exists
        # If path exists as a file, raise an error (can't create directory where file exists)
        if self.target_folder.exists() and self.target_folder.is_file():
            raise FileExistsError(
                f"Cannot create target directory: {self.target_folder} exists as a file"
            )
        
        # Try to create target directory with better error handling
        try:
            self.target_folder.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            return {
                "success": False,
                "source": str(file.full_path),
                "target": str(target_path),
                "message": f"Permission denied creating target directory {self.target_folder}: {e}",
            }
        except OSError as e:
            return {
                "success": False,
                "source": str(file.full_path),
                "target": str(target_path),
                "message": f"Failed to create target directory {self.target_folder}: {e}",
            }

        # Copy file
        # Note: We don't use os.access() checks here because they can give false negatives
        # on WSL mounts. The actual copy operation will fail with a proper error if there
        # are real permission issues.
        try:
            shutil.copy2(file.full_path, target_path)
            # Verify the copy actually succeeded by checking if target exists and has content
            if not target_path.exists():
                return {
                    "success": False,
                    "source": str(file.full_path),
                    "target": str(target_path),
                    "message": f"Copy appeared to succeed but target file does not exist",
                }
            if target_path.stat().st_size == 0 and file.file_size > 0:
                return {
                    "success": False,
                    "source": str(file.full_path),
                    "target": str(target_path),
                    "message": f"Copy appeared to succeed but target file is empty",
                }
            return {
                "success": True,
                "source": str(file.full_path),
                "target": str(target_path),
                "message": "Copied successfully",
            }
        except PermissionError as e:
            return {
                "success": False,
                "source": str(file.full_path),
                "target": str(target_path),
                "message": f"Permission denied copying file: {e}",
            }
        except OSError as e:
            # OSError includes Errno 1 (Operation not permitted) and other filesystem errors
            return {
                "success": False,
                "source": str(file.full_path),
                "target": str(target_path),
                "message": f"Filesystem error copying file: {e}",
            }
        except Exception as e:
            return {
                "success": False,
                "source": str(file.full_path),
                "target": str(target_path),
                "message": f"Error copying: {e}",
            }

    def copy_all(self, dry_run: bool = False) -> Dict[str, any]:
        """
        Copy all files from CSV to target folder.

        Args:
            dry_run: If True, don't actually copy, just return what would be done

        Returns:
            Dictionary with statistics: 'total', 'success', 'failed', 'skipped', 'results'
        """
        files = self.load_files_from_csv()

        stats = {"total": len(files), "success": 0, "failed": 0, "skipped": 0, "results": []}

        for file in files:
            result = self.copy_file(file, dry_run=dry_run)
            stats["results"].append(result)

            if result["success"]:
                stats["success"] += 1
            elif "skipping" in result["message"].lower():
                stats["skipped"] += 1
            else:
                stats["failed"] += 1

        return stats
