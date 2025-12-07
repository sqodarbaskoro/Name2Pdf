"""
Setup script for PDF Renamer by Visible Title
"""
from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="pdf-renamer",
    version="1.0.0",
    author="Sri Yanto Qodarbaskoro",
    author_email="sqodarbaskoro@gmail.com",
    description="A desktop application that renames PDF files based on visible title text",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sqodarbaskoro/pdf-renamer",
    py_modules=["Name2Pdf"],
    install_requires=[
        "pypdf>=3.17.0",
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Office/Business",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    entry_points={
        "console_scripts": [
            "pdf-renamer=Name2Pdf:main",
        ],
    },
)

