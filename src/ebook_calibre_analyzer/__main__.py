"""
CLI entry point for ebook-calibre-analyzer.
"""

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

from loguru import logger

from .cli import create_parser, get_default_output_path, parse_size
from .comparison import LibraryComparator
from .copier import FileCopier
from .csv_handler import CSVHandler
from .discovery import discover_files_recursive
from .hashing import CPUHashProcessor
from .hashing.orchestrator import HashingOrchestrator
from .models import EbookFile, FileCollection
from .preprocessing import preprocess_files
from .utils import get_default_file_extensions


def _configure_logging(verbose: bool = False) -> None:
    """Configure loguru logging for CLI."""
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="DEBUG" if verbose else "INFO",
        colorize=True,
    )


def run_analyze(args) -> int:
    """Run analyze command."""
    _configure_logging(verbose=args.verbose)

    ebooks_path = Path(args.ebooks_folder).resolve()
    calibre_path = Path(args.calibre_library_folder).resolve()

    # Validate paths
    if not ebooks_path.exists():
        logger.error(f"Ebooks folder does not exist: {ebooks_path}")
        return 1

    if not calibre_path.exists():
        logger.error(f"Calibre library folder does not exist: {calibre_path}")
        return 1

    # Determine output path
    if args.output:
        output_path = Path(args.output).resolve()
        # If path has no extension, always treat as directory
        if not output_path.suffix:
            # If it exists as a file, create directory with _dir suffix
            if output_path.exists() and output_path.is_file():
                logger.warning(
                    f"Output path exists as a file: {output_path}. "
                    f"Creating directory with _dir suffix: {output_path}_dir"
                )
                output_path = Path(str(output_path) + "_dir")
            # Create directory if it doesn't exist
            if not output_path.exists():
                output_path.mkdir(parents=True, exist_ok=True)
            # Create CSV file inside the directory
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_path = output_path / f"missing_from_calibre_{timestamp}.csv"
        # If path exists and is a directory, create CSV file inside it
        elif output_path.exists() and output_path.is_dir():
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            output_path = output_path / f"missing_from_calibre_{timestamp}.csv"
        # If path has extension, treat as file path
        else:
            # Create parent directory if needed
            if not output_path.parent.exists():
                output_path.parent.mkdir(parents=True, exist_ok=True)
            # Ensure .csv extension
            if output_path.suffix.lower() != ".csv":
                output_path = output_path.with_suffix(".csv")
    else:
        output_path = get_default_output_path()

    # Determine file extensions
    if args.file_types:
        file_extensions = args.file_types
    else:
        file_extensions = [ext.replace(".", "") for ext in get_default_file_extensions()]

    # Check for resume mode
    processed_files = set()

    if args.resume is not None:
        resume_path = Path(args.resume).resolve()
        if not resume_path.exists():
            logger.error(f"Resume CSV file does not exist: {resume_path}")
            return 1
        csv_handler = CSVHandler(resume_path, resume_mode=True)
        processed_files = csv_handler.get_processed_files()
        output_path = resume_path
        logger.info(f"Resuming from: {resume_path}")
        logger.info(f"Found {len(processed_files)} already processed files")
    else:
        csv_handler = CSVHandler(output_path, batch_size=args.batch_size, resume_mode=False)

    logger.info(f"Output CSV: {output_path}")
    logger.info(f"File extensions: {', '.join(file_extensions)}")

    # Discover files
    logger.info("Discovering files in ebooks folder...")
    ebooks_files = discover_files_recursive(ebooks_path, file_extensions, processed_files)
    logger.info(f"Found {len(ebooks_files)} files in ebooks folder")

    logger.info("Discovering files in Calibre library...")
    # Also apply processed_files exclusion to Calibre files (they could change between runs)
    calibre_files = discover_files_recursive(calibre_path, file_extensions, processed_files)
    logger.info(f"Found {len(calibre_files)} files in Calibre library")

    # Preprocessing: GPU/CPU selection (must happen before building collections)
    gpu_available = args.use_gpu
    # Only parse threshold if GPU is requested (threshold is only used when GPU is available)
    gpu_threshold = parse_size(args.gpu_threshold) if args.use_gpu else None

    logger.info("Categorizing files for processing...")
    categorized = preprocess_files(
        ebooks_files,
        gpu_available=gpu_available,
        gpu_threshold=gpu_threshold,
        processed_files=processed_files,
    )
    logger.info(f"  GPU: {len(categorized['gpu'])} files")
    logger.info(f"  CPU: {len(categorized['cpu'])} files")
    logger.info(f"  Skip: {len(categorized['skip'])} files (already processed)")

    # Build collections (only include files that aren't skipped)
    logger.debug("Building file collections...")
    ebooks_collection = FileCollection()
    # Only add files that aren't skipped (skip files are already in CSV)
    files_to_process = categorized["gpu"] + categorized["cpu"]
    for file in files_to_process:
        ebooks_collection.add_file(file)

    calibre_collection = FileCollection()
    for file in calibre_files:
        calibre_collection.add_file(file)

    # Initialize hash processors
    cpu_processor = CPUHashProcessor(num_workers=args.workers)
    gpu_processor = None

    # Check GPU availability - GPUHashProcessor will handle the check internally
    if gpu_available:
        try:
            from .hashing import GPUHashProcessor

            gpu_processor = GPUHashProcessor(device_id=args.gpu_device)
            if gpu_processor._gpu_available:
                logger.info("GPU hash processor available")
            else:
                error_reason = getattr(gpu_processor.gpu_pool, "_error_reason", "Unknown error")
                logger.warning(f"GPU requested but not available: {error_reason}")
                logger.warning("Falling back to CPU only")
                gpu_processor = None
                gpu_available = False  # Update flag since GPU is not actually available
        except (ImportError, RuntimeError) as e:
            logger.warning(f"GPU requested but not available: {e}")
            logger.warning("Falling back to CPU only")
            gpu_processor = None
            gpu_available = False  # Update flag since GPU is not actually available

    if gpu_processor is None:
        logger.info("Using CPU hash processor only")

    # Initialize hashing orchestrator (preprocessing)
    hashing_orchestrator = HashingOrchestrator(
        ebooks_collection=ebooks_collection,
        calibre_collection=calibre_collection,
        cpu_processor=cpu_processor,
        gpu_processor=gpu_processor,
    )

    # Initialize library comparator (pure comparison logic)
    comparator = LibraryComparator(
        ebooks_collection=ebooks_collection,
        calibre_collection=calibre_collection,
    )

    # Stage 1: Size comparison
    logger.info("Stage 1: Size comparison...")
    stage1_unique, stage2_candidates = comparator.stage1.compare()
    logger.info(f"  {len(stage1_unique)} files unique by size")
    logger.info(f"  {len(stage2_candidates)} files need further checking")

    # Stage 2: First 1KB hash comparison
    stage2_unique = []
    stage3_candidates = []
    if stage2_candidates:
        logger.info("Stage 2: First 1KB hash comparison...")

        # Preprocessing: Hash files for Stage 2
        hashing_orchestrator.hash_stage2_files(stage2_candidates)

        # Comparison: Compare hashed files
        stage2_unique, stage3_candidates = comparator.stage2.compare(stage2_candidates)
        logger.info(f"  {len(stage2_unique)} files unique by 1KB hash")
        logger.info(f"  {len(stage3_candidates)} files need full hash comparison")
        logger.info("")  # Empty line for readability

    # Stage 3: Full file hash comparison
    stage3_unique = []
    if stage3_candidates:
        logger.info("Stage 3: Full file hash comparison...")

        # Preprocessing: Hash files for Stage 3
        hashing_orchestrator.hash_stage3_files(
            stage3_candidates,
            gpu_available=gpu_available,
            gpu_threshold=gpu_threshold,
            processed_files=processed_files,
        )

        # Comparison: Compare hashed files
        stage3_unique = comparator.stage3.compare(stage3_candidates)

    # Collect all unique files
    unique_files = stage1_unique + stage2_unique + stage3_unique

    # Deduplicate: Remove duplicates within the datalake (same content, different paths)
    # Use full_hash if available, otherwise size+1k_hash, otherwise size only
    seen_hashes: Dict[bytes, EbookFile] = {}
    seen_size_1k: Dict[Tuple[int, bytes], EbookFile] = {}
    seen_sizes: Dict[int, EbookFile] = {}
    deduplicated_files = []
    duplicates_report: List[Dict[str, str]] = []  # Track duplicates for report

    for file in unique_files:
        # Prefer full hash for deduplication
        if file.full_hash and file.full_hash:
            if file.full_hash not in seen_hashes:
                seen_hashes[file.full_hash] = file
                deduplicated_files.append(file)
            else:
                original = seen_hashes[file.full_hash]
                duplicates_report.append(
                    {
                        "duplicate_path": str(file.full_path),
                        "original_path": str(original.full_path),
                        "method": "full_hash",
                        "file_size": str(file.file_size),
                        "filename": file.filename,
                    }
                )
                logger.debug(
                    f"Skipping duplicate (full hash): {file.full_path} "
                    f"(duplicate of {original.full_path})"
                )
        # Fallback to size + 1KB hash
        elif file.first_1k_hash:
            key = (file.get_size_hash(), file.first_1k_hash)
            if key not in seen_size_1k:
                seen_size_1k[key] = file
                deduplicated_files.append(file)
            else:
                original = seen_size_1k[key]
                duplicates_report.append(
                    {
                        "duplicate_path": str(file.full_path),
                        "original_path": str(original.full_path),
                        "method": "size+1k_hash",
                        "file_size": str(file.file_size),
                        "filename": file.filename,
                    }
                )
                logger.debug(
                    f"Skipping duplicate (size+1k): {file.full_path} "
                    f"(duplicate of {original.full_path})"
                )
        # Fallback to size only (Stage 1 files)
        else:
            size_key = file.get_size_hash()
            if size_key not in seen_sizes:
                seen_sizes[size_key] = file
                deduplicated_files.append(file)
            else:
                original = seen_sizes[size_key]
                duplicates_report.append(
                    {
                        "duplicate_path": str(file.full_path),
                        "original_path": str(original.full_path),
                        "method": "size_only",
                        "file_size": str(file.file_size),
                        "filename": file.filename,
                    }
                )
                logger.debug(
                    f"Skipping duplicate (size): {file.full_path} "
                    f"(duplicate of {original.full_path})"
                )

    # Deduplicate and write CSV (always deduplicate, even if no duplicates found)
    if len(deduplicated_files) < len(unique_files):
        duplicates_removed = len(unique_files) - len(deduplicated_files)
        logger.info(
            f"Deduplicating datalake files: {len(unique_files)} -> {len(deduplicated_files)} "
            f"({duplicates_removed} duplicates removed)"
        )
    else:
        logger.debug("No duplicates found in datalake")

    # Write deduplicated files to CSV (overwrite any existing file)
    # Delete existing file first to ensure clean overwrite
    if output_path.exists():
        output_path.unlink()
    final_csv_handler = CSVHandler(output_path, batch_size=args.batch_size, resume_mode=False)
    final_csv_handler.write_batch(deduplicated_files)
    final_csv_handler.flush()
    unique_files = deduplicated_files

    # Write duplicates report if duplicates were found
    if duplicates_report:
        duplicates_report_path = output_path.parent / f"{output_path.stem}_duplicates.csv"
        import csv as csv_module

        with open(duplicates_report_path, "w", newline="", encoding="utf-8") as f:
            writer = csv_module.DictWriter(
                f,
                fieldnames=[
                    "duplicate_path",
                    "original_path",
                    "method",
                    "file_size",
                    "filename",
                ],
            )
            writer.writeheader()
            writer.writerows(duplicates_report)
        logger.info(f"Duplicates report written to: {duplicates_report_path}")

    logger.info(f"Analysis complete. Results written to: {output_path}")
    logger.info(f"Total unique files: {len(unique_files)}")
    logger.info(f"  Stage 1 (size): {len(stage1_unique)}")
    if stage2_candidates:
        logger.info(f"  Stage 2 (1KB hash): {len(stage2_unique)}")
        if stage3_candidates:
            logger.info(f"  Stage 3 (full hash): {len(stage3_unique)}")

    return 0


def run_copy(args) -> int:
    """Run copy command."""
    _configure_logging(verbose=args.verbose)

    csv_path = Path(args.csv_file).resolve()
    ebooks_path = Path(args.ebooks_folder).resolve()
    target_path = Path(args.target_folder).resolve()

    # Validate paths
    if not csv_path.exists():
        logger.error(f"CSV file does not exist: {csv_path}")
        return 1

    if not ebooks_path.exists():
        logger.error(f"Ebooks folder does not exist: {ebooks_path}")
        return 1

    # Validate target path
    if target_path.exists() and target_path.is_file():
        logger.error(
            f"Target path exists as a file: {target_path}. "
            f"Please specify a directory path or remove/rename the file."
        )
        return 1

    # Create copier
    copier = FileCopier(
        csv_path=csv_path,
        source_base=ebooks_path,
        target_folder=target_path,
        conflict_handling=args.conflict_handling,
        num_workers=args.workers,
    )

    logger.info(f"CSV file: {csv_path}")
    logger.info(f"Source: {ebooks_path}")
    logger.info(f"Target: {target_path}")
    logger.info(f"Conflict handling: {args.conflict_handling}")

    if args.dry_run:
        logger.warning("DRY RUN - No files will be copied")

    # Copy files
    stats = copier.copy_all(dry_run=args.dry_run)

    # Print results
    logger.info(f"Total files: {stats['total']}")
    logger.info(f"Success: {stats['success']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info(f"Skipped: {stats['skipped']}")

    if args.verbose:
        logger.debug("Detailed results:")
        for result in stats["results"]:
            status = "✓" if result["success"] else "✗"
            logger.debug(f"  {status} {result['source']} -> {result.get('target', 'N/A')}")
            if result.get("message"):
                logger.debug(f"    {result['message']}")

    return 0 if stats["failed"] == 0 else 1


def main() -> int:
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if args.command == "analyze":
        return run_analyze(args)
    elif args.command == "copy":
        return run_copy(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
