"""
Base hash processor interface.
"""

from abc import ABC, abstractmethod
from typing import List

from ..models import EbookFile


class HashProcessor(ABC):
    """Abstract base class for hash processors."""

    @abstractmethod
    def hash_first_1k(self, file: EbookFile) -> bytes:
        """
        Hash the first 1KB of a file.

        Args:
            file: EbookFile to hash

        Returns:
            Hash bytes
        """
        pass

    @abstractmethod
    def hash_full_file(self, file: EbookFile) -> bytes:
        """
        Hash the entire file.

        Args:
            file: EbookFile to hash

        Returns:
            Hash bytes
        """
        pass

    @abstractmethod
    def hash_batch(self, files: List[EbookFile], stage: str) -> List[bytes]:
        """
        Hash a batch of files.

        Args:
            files: List of EbookFile objects to hash
            stage: Stage identifier ('1k' or 'full')

        Returns:
            List of hash bytes in same order as input files
        """
        pass
