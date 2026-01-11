"""
Hashing orchestrator for preprocessing files before comparison.

Handles all file hashing logic, determining which files to hash and when.
"""

from typing import List, Tuple

from loguru import logger

from ..models import EbookFile, FileCollection
from ..preprocessing import preprocess_files
from .base import HashProcessor


class HashingOrchestrator:
    """
    Orchestrates file hashing as a preprocessing step.

    Handles determining which files need hashing and coordinating
    the hash processors (CPU/GPU) to hash them.
    """

    def __init__(
        self,
        ebooks_collection: FileCollection,
        calibre_collection: FileCollection,
        cpu_processor: HashProcessor,
        gpu_processor: HashProcessor = None,
    ):
        """
        Initialize hashing orchestrator.

        Args:
            ebooks_collection: FileCollection from ebooks folder
            calibre_collection: FileCollection from calibre library
            cpu_processor: CPU hash processor
            gpu_processor: Optional GPU hash processor
        """
        self.ebooks_collection = ebooks_collection
        self.calibre_collection = calibre_collection
        self.cpu_processor = cpu_processor
        self.gpu_processor = gpu_processor

    def hash_stage2_files(
        self, stage2_candidates: List[EbookFile]
    ) -> Tuple[List[EbookFile], List[EbookFile]]:
        """
        Hash files for Stage 2 comparison (1KB hash).

        Args:
            stage2_candidates: Ebooks files that need 1KB hashing

        Returns:
            Tuple of (calibre_candidates, ebooks_candidates) that were hashed
        """
        # Find Calibre files that match sizes (for comparison)
        stage2_sizes = {f.get_size_hash() for f in stage2_candidates}
        calibre_stage2_candidates = []
        for file in self.calibre_collection.files:
            if file.get_size_hash() in stage2_sizes:
                calibre_stage2_candidates.append(file)

        # Hash Calibre files first (1KB only) - always use CPU for 1KB
        if calibre_stage2_candidates:
            logger.info(f"  Hashing {len(calibre_stage2_candidates)} Calibre files (1KB)...")
            calibre_1k_hashes = self.cpu_processor.hash_batch(calibre_stage2_candidates, "1k")
            for file, hash_value in zip(calibre_stage2_candidates, calibre_1k_hashes):
                if hash_value:  # Only set if hash succeeded
                    file.first_1k_hash = hash_value
                    # Update collection index
                    self.calibre_collection.by_size_and_1k[
                        (file.get_size_hash(), hash_value)
                    ].append(file)

        # Hash ebooks files (1KB only) - always use CPU for 1KB
        logger.info(f"  Hashing {len(stage2_candidates)} ebooks files (1KB)...")
        ebooks_1k_hashes = self.cpu_processor.hash_batch(stage2_candidates, "1k")
        for file, hash_value in zip(stage2_candidates, ebooks_1k_hashes):
            if hash_value:  # Only set if hash succeeded
                file.first_1k_hash = hash_value
                # Update collection index
                self.ebooks_collection.by_size_and_1k[(file.get_size_hash(), hash_value)].append(
                    file
                )

        return calibre_stage2_candidates, stage2_candidates

    def hash_stage3_files(
        self,
        stage3_candidates: List[EbookFile],
        gpu_available: bool = False,
        gpu_threshold: int = None,
        processed_files: set = None,
    ) -> Tuple[List[EbookFile], List[EbookFile]]:
        """
        Hash files for Stage 3 comparison (full hash).

        Args:
            stage3_candidates: Ebooks files that need full hashing
            gpu_available: Whether GPU is available
            gpu_threshold: GPU threshold for file size
            processed_files: Set of processed files for resume mode

        Returns:
            Tuple of (calibre_candidates, ebooks_candidates) that were hashed
        """
        # Split ebooks candidates by processing method (GPU/CPU)
        stage3_gpu_files = [
            f
            for f in stage3_candidates
            if f.processing_method == "gpu" and self.gpu_processor is not None
        ]
        stage3_cpu_files = [
            f
            for f in stage3_candidates
            if f.processing_method == "cpu" or self.gpu_processor is None
        ]

        logger.info(f"  GPU candidates: {len(stage3_gpu_files)}")
        logger.info(f"  CPU candidates: {len(stage3_cpu_files)}")

        # Find Calibre files that match size and 1KB hash
        stage3_size_1k_set = {
            (f.get_size_hash(), f.first_1k_hash)
            for f in stage3_candidates
            if f.first_1k_hash is not None
        }
        calibre_stage3_candidates = []
        for file in self.calibre_collection.files:
            if (
                file.first_1k_hash is not None
                and (file.get_size_hash(), file.first_1k_hash) in stage3_size_1k_set
            ):
                calibre_stage3_candidates.append(file)

        # Preprocess Calibre files for GPU/CPU selection
        calibre_categorized = preprocess_files(
            calibre_stage3_candidates,
            gpu_available=gpu_available,
            gpu_threshold=gpu_threshold,
            processed_files=processed_files or set(),
        )
        calibre_stage3_gpu_files = calibre_categorized["gpu"]
        calibre_stage3_cpu_files = calibre_categorized["cpu"]

        logger.info(f"  Calibre GPU candidates: {len(calibre_stage3_gpu_files)}")
        logger.info(f"  Calibre CPU candidates: {len(calibre_stage3_cpu_files)}")

        # Hash Calibre files (full hash) - split by GPU/CPU
        # Process Calibre GPU files
        if calibre_stage3_gpu_files and self.gpu_processor:
            logger.info(f"  Hashing {len(calibre_stage3_gpu_files)} Calibre files on GPU (full)...")
            calibre_gpu_hashes = self.gpu_processor.hash_batch(calibre_stage3_gpu_files, "full")
            for file, hash_value in zip(calibre_stage3_gpu_files, calibre_gpu_hashes):
                if hash_value:  # Only set if hash succeeded
                    file.full_hash = hash_value
                    # Update collection index
                    self.calibre_collection.by_full_hash[hash_value] = file

        # Process Calibre CPU files
        if calibre_stage3_cpu_files:
            logger.info(f"  Hashing {len(calibre_stage3_cpu_files)} Calibre files on CPU (full)...")
            calibre_cpu_hashes = self.cpu_processor.hash_batch(calibre_stage3_cpu_files, "full")
            for file, hash_value in zip(calibre_stage3_cpu_files, calibre_cpu_hashes):
                if hash_value:  # Only set if hash succeeded
                    file.full_hash = hash_value
                    # Update collection index
                    self.calibre_collection.by_full_hash[hash_value] = file

        # Hash ebooks files (full hash) - split by GPU/CPU
        # Process GPU files
        if stage3_gpu_files and self.gpu_processor:
            logger.info(f"  Hashing {len(stage3_gpu_files)} ebooks files on GPU (full)...")
            gpu_hashes = self.gpu_processor.hash_batch(stage3_gpu_files, "full")
            for file, hash_value in zip(stage3_gpu_files, gpu_hashes):
                if hash_value:  # Only set if hash succeeded
                    file.full_hash = hash_value
                    # Update collection index
                    self.ebooks_collection.by_full_hash[hash_value] = file

        # Process CPU files
        if stage3_cpu_files:
            logger.info(f"  Hashing {len(stage3_cpu_files)} ebooks files on CPU (full)...")
            cpu_hashes = self.cpu_processor.hash_batch(stage3_cpu_files, "full")
            for file, hash_value in zip(stage3_cpu_files, cpu_hashes):
                if hash_value:  # Only set if hash succeeded
                    file.full_hash = hash_value
                    # Update collection index
                    self.ebooks_collection.by_full_hash[hash_value] = file

        return calibre_stage3_candidates, stage3_candidates
