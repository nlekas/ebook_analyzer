"""
OOP classes for ebook file representation and collections.
"""

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class EbookFile:
    """Represents a single ebook file with all its metadata and processing state."""

    full_path: Path
    relative_path: Path
    filename: str
    file_size: int
    file_extension: str
    size_hash: Optional[int] = None  # For Stage 1
    first_1k_hash: Optional[bytes] = None  # For Stage 2
    full_hash: Optional[bytes] = None  # For Stage 3
    processing_method: str = "cpu"  # 'cpu' | 'gpu' | 'skip'
    processing_status: str = (
        "pending"  # 'pending' | 'size_checked' | '1k_hashed' | 'full_hashed' | 'error'
    )
    error_message: Optional[str] = None

    def get_size_hash(self) -> int:
        """Get file size (used as hash for Stage 1)."""
        if self.size_hash is None:
            self.size_hash = self.file_size
        return self.size_hash

    def to_dict(self) -> dict:
        """Convert to dictionary for CSV serialization."""
        return {
            "relative_path": str(self.relative_path),
            "filename": self.filename,
            "file_size": self.file_size,
            "full_path": str(self.full_path),
        }

    @classmethod
    def from_dict(cls, data: dict, base_path: Path) -> "EbookFile":
        """Create EbookFile from dictionary (CSV deserialization)."""
        full_path = Path(data["full_path"])
        relative_path = Path(data["relative_path"])

        return cls(
            full_path=full_path,
            relative_path=relative_path,
            filename=data["filename"],
            file_size=int(data["file_size"]),
            file_extension=full_path.suffix.lower(),
        )


class FileCollection:
    """Manages collections of EbookFile objects with efficient lookups."""

    def __init__(self):
        self.files: List[EbookFile] = []
        self.by_size: Dict[int, List[EbookFile]] = defaultdict(list)
        self.by_size_and_1k: Dict[Tuple[int, bytes], List[EbookFile]] = defaultdict(list)
        self.by_full_hash: Dict[bytes, EbookFile] = {}

    def add_file(self, file: EbookFile) -> None:
        """Add a file to the collection."""
        self.files.append(file)
        size = file.get_size_hash()
        self.by_size[size].append(file)

        if file.first_1k_hash is not None:
            self.by_size_and_1k[(size, file.first_1k_hash)].append(file)

        if file.full_hash is not None:
            self.by_full_hash[file.full_hash] = file

    def get_files_by_size(self, size: int) -> List[EbookFile]:
        """Get all files with the given size."""
        return self.by_size.get(size, [])

    def get_files_by_size_and_1k(self, size: int, hash_1k: bytes) -> List[EbookFile]:
        """Get all files with the given size and first 1KB hash."""
        return self.by_size_and_1k.get((size, hash_1k), [])

    def get_file_by_full_hash(self, hash_value: bytes) -> Optional[EbookFile]:
        """Get file by full hash, or None if not found."""
        return self.by_full_hash.get(hash_value)

    def get_unique_sizes(self) -> Set[int]:
        """Get set of all unique file sizes."""
        return set(self.by_size.keys())
