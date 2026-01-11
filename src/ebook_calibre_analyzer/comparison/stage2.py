"""
Stage 2: First 1KB hash comparison.

Pure comparison logic - assumes files have already been hashed.
"""

from typing import List, Tuple

from ..models import EbookFile, FileCollection


class Stage2Comparator:
    """Compares files by size and first 1KB hash."""

    def __init__(self, ebooks_collection: FileCollection, calibre_collection: FileCollection):
        """
        Initialize Stage 2 comparator.

        Args:
            ebooks_collection: FileCollection from ebooks folder
            calibre_collection: FileCollection from calibre library
        """
        self.ebooks_collection = ebooks_collection
        self.calibre_collection = calibre_collection

    def compare(
        self, stage2_candidates: List[EbookFile]
    ) -> Tuple[List[EbookFile], List[EbookFile]]:
        """
        Compare files by first 1KB hash.

        Assumes files have already been hashed (preprocessing step).

        Args:
            stage2_candidates: Files that matched size in Stage 1 and have been hashed

        Returns:
            Tuple of (unique_files, candidates_for_stage3)
        """
        unique_files = []
        candidates = []

        for file in stage2_candidates:
            if file.first_1k_hash is None:
                # Hash failed - treat as unique to be safe
                unique_files.append(file)
                file.processing_status = "1k_hashed"
                continue

            calibre_matches = self.calibre_collection.get_files_by_size_and_1k(
                file.get_size_hash(), file.first_1k_hash
            )

            if not calibre_matches:
                # Unique by 1KB hash
                unique_files.append(file)
                file.processing_status = "1k_hashed"
            else:
                # Matches found - need full hash
                candidates.append(file)
                file.processing_status = "1k_hashed"

        return unique_files, candidates
