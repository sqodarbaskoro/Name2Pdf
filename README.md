# PDF Renamer by Visible Title

A production-ready desktop application that automatically renames PDF files based on the visible "Title" text found on the first page of each document.

## Features

- 🎯 **Automatic Title Detection**: Extracts titles from the first page of PDF files
- 📁 **Flexible Processing**: Rename in-place or copy to a new folder
- 🔄 **Duplicate Handling**: Automatically handles duplicate filenames with numbering
- 📊 **Progress Tracking**: Real-time progress bar and detailed logging
- 🛡️ **Error Handling**: Robust error handling with detailed error messages
- 📝 **Logging**: Comprehensive logging to both GUI and log files

## Requirements

- Python 3.8 or higher
- tkinter (usually included with Python)
- pypdf library

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Edit `config.json` to customize:
- Application name and version
- Author information (name, email, LinkedIn URL)
- Logging settings

## Usage

1. Run the application:
```bash
python Name2Pdf.py
```

2. Select the input folder containing PDF files

3. Choose output folder (or enable "Save in the same folder" for in-place renaming)

4. Click "Start Renaming" to begin processing

5. Monitor progress in the log area

## How It Works

The application:
1. Scans the selected folder for PDF files
2. Extracts text from the first page of each PDF
3. Searches for a line containing "title" (case-insensitive)
4. Uses the next non-empty line as the filename
5. Sanitizes the filename (removes illegal characters)
6. Renames or copies the file with the new name
7. Handles duplicates by appending a number (e.g., "Title (1).pdf")

## File Structure

```
Name2Pdf/
├── Name2Pdf.py          # Main application file
├── requirements.txt     # Python dependencies
├── config.json          # Configuration file
├── README.md            # This file
├── .gitignore          # Git ignore rules
└── setup.py            # Package setup (optional)
```

## Logging

Logs are written to:
- GUI log area (real-time)
- `logs/pdf_renamer.log` (if enabled in config.json)

## Error Handling

The application handles:
- Invalid PDF files
- Files without pages
- Missing title information
- Permission errors
- Duplicate filenames
- Invalid characters in filenames

## Development

### Building for Distribution

To create a distributable package:

```bash
python setup.py sdist bdist_wheel
```

### Running Tests

(Add your test suite here when available)

## License

[Specify your license here]

## Author

**Sri Yanto Qodarbaskoro**
- Email: sqodarbaskoro@gmail.com
- LinkedIn: [sqodarbaskoro](https://www.linkedin.com/in/sqodarbaskoro)

## Support

For issues, questions, or contributions, please open an issue on the repository or contact the author.

## Changelog

### Version 1.0.0
- Initial production release
- GUI-based PDF renaming tool
- Configurable settings
- Comprehensive logging
- Error handling and validation

