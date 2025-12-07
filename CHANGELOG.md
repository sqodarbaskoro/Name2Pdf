# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-12-XX

### Added
- Initial production release
- GUI-based PDF renaming tool with tkinter
- Automatic title extraction from PDF first page
- In-place renaming and copy-to-folder modes
- Progress bar and real-time status updates
- Comprehensive logging system (GUI and file logging)
- Configuration file support (config.json)
- Error handling and validation
- Duplicate filename handling with automatic numbering
- About window with author information
- Thread-safe GUI updates
- Type hints throughout codebase
- Documentation (README.md)
- Package setup (setup.py)
- License file (MIT)

### Features
- Scans folders for PDF files
- Extracts visible "Title" text from first page
- Sanitizes filenames (removes illegal characters)
- Handles duplicate filenames automatically
- Detailed logging and error reporting
- User-friendly GUI with progress tracking

