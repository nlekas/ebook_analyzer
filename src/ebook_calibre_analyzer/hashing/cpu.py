"""
CPU-based hash processor using multiprocessing.
"""

import hashlib
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List

from ..models import EbookFile
from .base import HashProcessor


def _hash_first_1k_worker(file_path: str) -> bytes:
    """Worker function for hashing first 1KB of a file."""
    try:
        hash_obj = hashlib.sha256()
        with open(file_path, "rb") as f:
            chunk = f.read(1024)
            hash_obj.update(chunk)
        return hash_obj.digest()
    except OSError:
        return b""


def _hash_full_file_worker(file_path: str) -> bytes:
    """Worker function for hashing entire file."""
    try:
        hash_obj = hashlib.sha256()
        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(1024 * 1024)  # Read in 1MB chunks
                if not chunk:
                    break
                hash_obj.update(chunk)
        return hash_obj.digest()
    except OSError:
        return b""


class CPUHashProcessor(HashProcessor):
    """Multiprocessing-based CPU hasher."""

    def __init__(self, num_workers: int = 10, chunk_size: int = 1024 * 1024):
        """
        Initialize CPU hash processor.

        Args:
            num_workers: Number of worker processes
            chunk_size: Chunk size for reading files (default: 1MB)
        """
        self.num_workers = num_workers
        self.chunk_size = chunk_size

    def hash_first_1k(self, file: EbookFile) -> bytes:
        """Hash the first 1KB of a file."""
        return _hash_first_1k_worker(str(file.full_path))

    def hash_full_file(self, file: EbookFile) -> bytes:
        """Hash the entire file."""
        return _hash_full_file_worker(str(file.full_path))

    def hash_batch(self, files: List[EbookFile], stage: str) -> List[bytes]:
        """
        Hash a batch of files using multiprocessing.

        Args:
            files: List of EbookFile objects to hash
            stage: Stage identifier ('1k' or 'full')

        Returns:
            List of hash bytes in same order as input files
        """
        if stage == "1k":
            worker_func = _hash_first_1k_worker
        elif stage == "full":
            worker_func = _hash_full_file_worker
        else:
            raise ValueError(f"Unknown stage: {stage}")

        results = [None] * len(files)
        file_paths = [str(f.full_path) for f in files]

        with ProcessPoolExecutor(max_workers=self.num_workers) as executor:
            # Submit all tasks
            future_to_index = {
                executor.submit(worker_func, path): i for i, path in enumerate(file_paths)
            }

            # Collect results
            for future in as_completed(future_to_index):
                index = future_to_index[future]
                try:
                    results[index] = future.result()
                except Exception:
                    results[index] = b""

        return results
