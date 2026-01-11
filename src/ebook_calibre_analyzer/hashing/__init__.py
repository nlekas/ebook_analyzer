"""Hashing module for ebook file processing."""

from .base import HashProcessor
from .cpu import CPUHashProcessor

__all__ = ["HashProcessor", "CPUHashProcessor"]

# GPU processor is optional
try:
    from .gpu import GPUHashProcessor

    __all__.append("GPUHashProcessor")
except ImportError:
    pass
