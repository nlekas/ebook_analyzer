"""
Stage 1: Size-based comparison.
"""

from typing import List, Tuple

from ..models import EbookFile, FileCollection


class Stage1Comparator:
    """Compares files by size only."""

    def __init__(self, ebooks_collection: FileCollection, calibre_collection: FileCollection):
        """
        Initialize Stage 1 comparator.

        Args:
            ebooks_collection: FileCollection from ebooks folder
            calibre_collection: FileCollection from calibre library
        """
        self.ebooks_collection = ebooks_collection
        self.calibre_collection = calibre_collection

    def compare(self) -> Tuple[List[EbookFile], List[EbookFile]]:
        """
        Compare files by size.

        Returns:
            Tuple of (unique_files, candidates_for_stage2)
        """
        calibre_sizes = self.calibre_collection.get_unique_sizes()
        unique_files = []
        candidates = []

        for file in self.ebooks_collection.files:
            if file.get_size_hash() not in calibre_sizes:
                # Unique by size - no need to hash
                unique_files.append(file)
                file.processing_status = "size_checked"
            else:
                # Size matches - need further checking
                candidates.append(file)
                file.processing_status = "size_checked"

        return unique_files, candidates
