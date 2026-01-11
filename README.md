# Ebook-Calibre Library Analyzer

A Python package to analyze ebook files in a datalake (ebooks folder) and compare them against a Calibre library to identify files that exist in the datalake but are not yet in the Calibre library.

## Features

- **Recursive file discovery** - Handles deeply nested directory structures
- **Efficient deduplication** - Three-stage hashing approach (size → 1KB hash → full hash)
- **Resume capability** - Can resume interrupted analysis from CSV checkpoints
- **GPU acceleration** - Optional GPU support for large file hashing (requires CUDA)
- **Auto GPU/CPU selection** - Intelligently selects processing method based on file characteristics
- **Flat copy structure** - Copies files to Calibre import folder in flat structure

## Installation

```bash
pip install -e .
```

For GPU support:
```bash
pip install -e ".[gpu]"
```

## Usage

### Analysis Command

Analyze ebooks folder and compare against Calibre library:

```bash
ebook-analyzer analyze <ebooks_folder> <calibre_library_folder> [OPTIONS]
```

Options:
- `--output, -o PATH` - Output CSV path (default: `./missing_from_calibre_YYYYMMDD_HHMMSS.csv`)
- `--file-types EXT [EXT ...]` - File extensions to include (default: pdf, cbr, cbz, epub, mobi, azw, azw3, fb2, lit, prc, txt, rtf, djvu, chm, html, htm)
- `--resume PATH` - Resume from existing CSV file
- `--use-gpu` - Enable GPU acceleration
- `--gpu-device ID` - GPU device ID (default: 0)
- `--gpu-threshold SIZE` - File size threshold for GPU (default: 100MB)
- `--batch-size N` - CSV write batch size (default: 100)
- `--workers N` - CPU worker processes (default: 10)
- `--verbose, -v` - Verbose output
- `--progress` - Show progress bars

### Copy Command

Copy files from CSV to Calibre import folder:

```bash
ebook-analyzer copy <csv_file> <ebooks_folder> <target_folder> [OPTIONS]
```

Options:
- `--dry-run` - Show what would be copied without copying
- `--conflict-handling MODE` - How to handle filename conflicts: rename, skip, overwrite (default: rename)
- `--workers N` - Parallel copy workers (default: 4)
- `--verbose, -v` - Verbose output
- `--progress` - Show progress bars

## Development

```bash
# Install in development mode with dev dependencies
pip install -e ".[dev]"

# Using tox (recommended - runs all checks in isolated environments)
tox -e lint          # Run ruff linter
tox -e format        # Check code formatting
tox -e format-fix    # Format code with black
tox -e ruff-fix      # Auto-fix ruff issues
tox -e typecheck     # Run mypy type checker
tox -e test          # Run pytest tests
tox -e build         # Build the package
tox -e all           # Run all checks (lint, format, typecheck, test)

# Or run individual tools directly
pytest tests/
black src/ tests/
ruff check src/ tests/
ruff check --fix src/ tests/
mypy src/
```

## License

MIT

