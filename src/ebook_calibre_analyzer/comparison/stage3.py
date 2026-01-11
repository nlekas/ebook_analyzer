"""
Stage 3: Full file hash comparison.

Pure comparison logic - assumes files have already been hashed.
"""

from typing import List

from loguru import logger

from ..models import EbookFile, FileCollection


class Stage3Comparator:
    """Compares files by full file hash."""

    def __init__(
        self,
        ebooks_collection: FileCollection,
        calibre_collection: FileCollection,
    ):
        """
        Initialize Stage 3 comparator.

        Args:
            ebooks_collection: FileCollection from ebooks folder
            calibre_collection: FileCollection from calibre library
        """
        self.ebooks_collection = ebooks_collection
        self.calibre_collection = calibre_collection

    def compare(self, stage3_candidates: List[EbookFile]) -> List[EbookFile]:
        """
        Compare files by full file hash.

        Assumes files have already been hashed (preprocessing step).

        Args:
            stage3_candidates: Files that matched size and 1KB hash in Stage 2 and have been hashed

        Returns:
            List of unique files
        """
        unique_files = []

        for file in stage3_candidates:
            # Get hash from file object (already set during hashing preprocessing)
            if file.full_hash is None or not file.full_hash:
                # Hash failed - treat as unique to be safe
                unique_files.append(file)
                file.processing_status = "full_hashed"
                continue

            calibre_match = self.calibre_collection.get_file_by_full_hash(file.full_hash)

            if calibre_match is None:
                # Unique by full hash
                unique_files.append(file)
                file.processing_status = "full_hashed"
            else:
                # Duplicate found - skip
                file.processing_status = "full_hashed"

        logger.info(f"  {len(unique_files)} files unique by full hash")
        logger.info(f"  {len(stage3_candidates) - len(unique_files)} duplicates found")

        return unique_files
