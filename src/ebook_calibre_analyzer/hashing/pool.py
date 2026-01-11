"""
GPU memory pool manager for handling large file hashing.
"""

from typing import Dict, Optional


class GPUMemoryPool:
    """
    Manages GPU memory allocation for large files.

    Handles chunked processing for files that don't fit in GPU memory.
    """

    def __init__(self, device_id: int = 0, max_file_size: int = 500_000_000_000):
        """
        Initialize GPU memory pool.

        Args:
            device_id: GPU device ID
            max_file_size: Maximum file size to handle (default: 500GB)
        """
        self.device_id = device_id
        self.max_file_size = max_file_size
        self.total_memory: Optional[int] = None
        self.available_memory: Optional[int] = None
        self.allocated_buffers: Dict[str, any] = {}  # file_id -> GPU buffer
        self._gpu_available = False
        self._error_reason: Optional[str] = None

        # Try to initialize GPU
        try:
            import cupy as cp

            # Set device
            cp.cuda.Device(device_id).use()
            # Query memory
            meminfo = cp.cuda.runtime.memGetInfo()
            self.total_memory = meminfo[1]  # Total memory
            self.available_memory = meminfo[0]  # Free memory
            self._gpu_available = True
        except ImportError:
            # CuPy not installed
            self._gpu_available = False
            self.total_memory = None
            self.available_memory = None
            self._error_reason = (
                "CuPy not installed. Install with: pip install 'ebook-calibre-analyzer[gpu]'"
            )
        except RuntimeError as e:
            # GPU/CUDA runtime error (e.g., no CUDA device, WSL CUDA not configured)
            self._gpu_available = False
            self.total_memory = None
            self.available_memory = None
            self._error_reason = f"CUDA runtime error: {e}"
        except Exception as e:
            # Other unexpected errors
            self._gpu_available = False
            self.total_memory = None
            self.available_memory = None
            self._error_reason = f"Unexpected error: {e}"

    def can_allocate(self, size: int) -> bool:
        """
        Check if we can allocate the requested size.

        Args:
            size: Size in bytes to allocate

        Returns:
            True if allocation is possible
        """
        if not self._gpu_available:
            return False

        # Reserve 10% of available memory for other operations
        available = self.get_available_memory()
        reserved = int(available * 0.1)
        return size <= (available - reserved)

    def get_available_memory(self) -> int:
        """
        Get available GPU memory.

        Returns:
            Available memory in bytes
        """
        if not self._gpu_available:
            return 0

        try:
            import cupy as cp

            cp.cuda.Device(self.device_id).use()
            meminfo = cp.cuda.runtime.memGetInfo()
            self.available_memory = meminfo[0]  # Free memory
            return self.available_memory
        except (ImportError, RuntimeError):
            return 0

    def cleanup(self) -> None:
        """Release all allocated buffers."""
        if self._gpu_available:
            try:
                import cupy as cp

                # Clear memory pool
                mempool = cp.get_default_memory_pool()
                mempool.free_all_blocks()
            except (ImportError, RuntimeError):
                pass

        self.allocated_buffers.clear()
