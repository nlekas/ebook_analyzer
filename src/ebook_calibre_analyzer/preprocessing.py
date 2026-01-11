"""
GPU/CPU selection preprocessing module.
"""

from typing import Dict, List, Optional

from .models import EbookFile


def preprocess_files(
    files: List[EbookFile],
    gpu_available: bool = False,
    gpu_threshold: Optional[int] = None,  # 100MB default, None if GPU not available
    processed_files: Optional[set] = None,
) -> Dict[str, List[EbookFile]]:
    """
    Categorize files for optimal processing method.

    Args:
        files: List of EbookFile objects to categorize
        gpu_available: Whether GPU is available
        gpu_threshold: File size threshold for GPU processing (bytes).
                      If None, defaults to 100MB when GPU is available.
        processed_files: Set of file paths already processed (for resume mode)

    Returns:
        Dictionary with keys:
        - 'gpu': List of files to process on GPU
        - 'cpu': List of files to process on CPU
        - 'skip': List of files to skip (already processed)
    """
    if processed_files is None:
        processed_files = set()

    # Default threshold if not provided and GPU is available
    if gpu_threshold is None and gpu_available:
        gpu_threshold = 100 * 1024 * 1024  # 100MB default

    categorized = {"gpu": [], "cpu": [], "skip": []}

    for file in files:
        # Skip if already processed (resume mode)
        if str(file.full_path) in processed_files:
            categorized["skip"].append(file)
            continue

        # Determine processing method
        # Only use GPU if available, threshold is set, and file is large enough
        if gpu_available and gpu_threshold is not None and file.file_size >= gpu_threshold:
            file.processing_method = "gpu"
            categorized["gpu"].append(file)
        else:
            file.processing_method = "cpu"
            categorized["cpu"].append(file)

    return categorized
