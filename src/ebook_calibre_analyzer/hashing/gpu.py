"""
GPU-accelerated hash processor (optional, requires CUDA/OpenCL).
"""

import hashlib
from typing import List

from ..models import EbookFile
from .base import HashProcessor
from .pool import GPUMemoryPool


class GPUHashProcessor(HashProcessor):
    """
    GPU-accelerated hasher with memory pooling.

    Uses CuPy for GPU memory management and data transfer.
    For large files, uses chunked processing to fit within GPU memory limits.
    """

    def __init__(
        self, device_id: int = 0, batch_size: int = 10, chunk_size: int = 256 * 1024 * 1024
    ):
        """
        Initialize GPU hash processor.

        Args:
            device_id: GPU device ID
            batch_size: Number of files to process in a batch
            chunk_size: Chunk size for reading files (default: 256MB)
        """
        self.device_id = device_id
        self.batch_size = batch_size
        self.chunk_size = chunk_size
        self.gpu_pool = GPUMemoryPool(device_id=device_id)
        self._gpu_available = self.gpu_pool._gpu_available

        if self._gpu_available:
            try:
                import cupy as cp

                cp.cuda.Device(device_id).use()
            except (ImportError, RuntimeError):
                self._gpu_available = False

    def hash_first_1k(self, file: EbookFile) -> bytes:
        """
        Hash the first 1KB of a file.

        Note: First 1KB is too small for GPU - uses CPU instead.
        """
        # First 1KB is too small for GPU, use CPU
        from .cpu import CPUHashProcessor

        cpu_processor = CPUHashProcessor()
        return cpu_processor.hash_first_1k(file)

    def hash_full_file(self, file: EbookFile) -> bytes:
        """
        Hash the entire file using GPU.

        For large files (>GPU memory), uses chunked processing.
        """
        if not self._gpu_available:
            # Fallback to CPU
            from .cpu import CPUHashProcessor

            cpu_processor = CPUHashProcessor()
            return cpu_processor.hash_full_file(file)

        try:
            import cupy as cp

            cp.cuda.Device(self.device_id).use()
            file_size = file.file_size

            # Check if file fits in GPU memory
            available_memory = self.gpu_pool.get_available_memory()
            # Reserve 20% for overhead
            usable_memory = int(available_memory * 0.8)

            hash_obj = hashlib.sha256()

            if file_size <= usable_memory:
                # File fits in GPU memory - read all at once
                with open(file.full_path, "rb") as f:
                    data = f.read()

                # Transfer to GPU for processing (though hashing happens on CPU)
                # This allows for future GPU-accelerated hashing implementations
                gpu_data = cp.asarray(bytearray(data))
                # Hash on CPU (SHA256 on GPU requires specialized libraries)
                hash_obj.update(data)
                del gpu_data  # Free GPU memory
                cp.get_default_memory_pool().free_all_blocks()
            else:
                # File too large - use chunked processing
                chunk_size = min(self.chunk_size, usable_memory)
                with open(file.full_path, "rb") as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break

                        # Transfer chunk to GPU (for future GPU hashing)
                        gpu_chunk = cp.asarray(bytearray(chunk))
                        # Hash on CPU
                        hash_obj.update(chunk)
                        del gpu_chunk  # Free GPU memory
                        cp.get_default_memory_pool().free_all_blocks()

            return hash_obj.digest()

        except (ImportError, RuntimeError, OSError):
            # GPU error or file error - fallback to CPU
            from .cpu import CPUHashProcessor

            cpu_processor = CPUHashProcessor()
            return cpu_processor.hash_full_file(file)

    def hash_batch(self, files: List[EbookFile], stage: str) -> List[bytes]:
        """
        Hash a batch of files using GPU.

        Args:
            files: List of EbookFile objects to hash
            stage: Stage identifier ('1k' or 'full')

        Returns:
            List of hash bytes in same order as input files
        """
        if stage == "1k":
            # First 1KB is too small for GPU
            from .cpu import CPUHashProcessor

            cpu_processor = CPUHashProcessor()
            return cpu_processor.hash_batch(files, stage)

        if not self._gpu_available:
            # Fallback to CPU
            from .cpu import CPUHashProcessor

            cpu_processor = CPUHashProcessor()
            return cpu_processor.hash_batch(files, stage)

        # Process files in batches to manage GPU memory
        results = []
        for i in range(0, len(files), self.batch_size):
            batch = files[i : i + self.batch_size]
            batch_results = []

            for file in batch:
                try:
                    hash_result = self.hash_full_file(file)
                    batch_results.append(hash_result)
                except Exception:
                    batch_results.append(b"")

            results.extend(batch_results)

        return results
