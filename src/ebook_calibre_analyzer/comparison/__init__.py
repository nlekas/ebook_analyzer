"""
Library comparison module with compositional pattern.

Provides staged comparison logic for finding unique files.
Pure comparison logic - assumes files have already been hashed.
"""

from typing import List

from ..models import EbookFile, FileCollection
from .stage1 import Stage1Comparator
from .stage2 import Stage2Comparator
from .stage3 import Stage3Comparator


class LibraryComparator:
    """
    Orchestrates three-stage comparison to find unique files.

    Uses compositional pattern with separate comparators for each stage.
    Comparison logic only - hashing is handled separately as preprocessing.
    """

    def __init__(
        self,
        ebooks_collection: FileCollection,
        calibre_collection: FileCollection,
    ):
        """
        Initialize library comparator.

        Args:
            ebooks_collection: FileCollection from ebooks folder
            calibre_collection: FileCollection from calibre library
        """
        self.ebooks_collection = ebooks_collection
        self.calibre_collection = calibre_collection

        # Initialize stage comparators (no hash processors - hashing is separate)
        self.stage1 = Stage1Comparator(ebooks_collection, calibre_collection)
        self.stage2 = Stage2Comparator(ebooks_collection, calibre_collection)
        self.stage3 = Stage3Comparator(ebooks_collection, calibre_collection)

    def find_unique_files(self) -> List[EbookFile]:
        """
        Find all unique files by orchestrating three-stage comparison.

        Assumes files have already been hashed (if needed for later stages).
        Files without hashes will be skipped in later stages.

        Returns:
            List of unique EbookFile objects
        """
        all_unique = []

        # Stage 1: Size comparison
        stage1_unique, stage2_candidates = self.stage1.compare()
        all_unique.extend(stage1_unique)

        # Stage 2: First 1KB hash comparison (only if hashes are available)
        if stage2_candidates:
            # Filter to files that have 1KB hashes
            stage2_candidates_with_hash = [
                f for f in stage2_candidates if f.first_1k_hash is not None
            ]
            if stage2_candidates_with_hash:
                stage2_unique, stage3_candidates = self.stage2.compare(stage2_candidates_with_hash)
                all_unique.extend(stage2_unique)

                # Stage 3: Full file hash comparison (only if hashes are available)
                if stage3_candidates:
                    # Filter to files that have full hashes
                    stage3_candidates_with_hash = [
                        f for f in stage3_candidates if f.full_hash is not None
                    ]
                    if stage3_candidates_with_hash:
                        stage3_unique = self.stage3.compare(stage3_candidates_with_hash)
                        all_unique.extend(stage3_unique)

        return all_unique
