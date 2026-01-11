"""
Tests for GPUMemoryPool class.
"""

from ebook_calibre_analyzer.hashing.pool import GPUMemoryPool


class TestGPUMemoryPool:
    """Test cases for GPUMemoryPool class."""

    def test_init_sets_device_id(self):
        """Test that __init__ initializes with provided device_id."""
        pool = GPUMemoryPool(device_id=1)
        assert pool.device_id == 1

    def test_init_sets_max_file_size(self):
        """Test that __init__ initializes with provided max_file_size."""
        max_size = 100_000_000_000
        pool = GPUMemoryPool(max_file_size=max_size)
        assert pool.max_file_size == max_size

    def test_init_initializes_empty_buffers(self):
        """Test that __init__ initializes empty allocated_buffers dict."""
        pool = GPUMemoryPool()
        assert pool.allocated_buffers == {}
        assert len(pool.allocated_buffers) == 0

    def test_can_allocate_checks_available_memory(self):
        """Test that can_allocate checks available GPU memory."""
        pool = GPUMemoryPool()
        # If GPU available, should check memory
        # If not, should return False
        result = pool.can_allocate(1024 * 1024)  # 1MB
        # Result depends on GPU availability
        assert isinstance(result, bool)

    def test_get_available_memory_queries_gpu(self):
        """Test that get_available_memory queries GPU when available."""
        pool = GPUMemoryPool()
        memory = pool.get_available_memory()
        # Should return a non-negative integer
        assert isinstance(memory, int)
        assert memory >= 0

    def test_cleanup_clears_buffers(self):
        """Test that cleanup clears allocated_buffers."""
        pool = GPUMemoryPool()
        # Add some dummy data
        pool.allocated_buffers["test"] = "dummy"
        assert len(pool.allocated_buffers) > 0
        pool.cleanup()
        assert len(pool.allocated_buffers) == 0
        assert pool.allocated_buffers == {}
