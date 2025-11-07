"""
Setup script for LENR Research Collection System
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lenr-collection",
    version="1.0.0",
    author="LENR Research Team",
    description="Automated LENR research paper collection and verification system",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/lenr-collection",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "pandas>=2.0.0",
        "openpyxl>=3.1.0",
        "requests>=2.31.0",
        "beautifulsoup4>=4.12.0",
        "aiohttp>=3.9.0",
        "pymupdf>=1.23.0",
        "arxiv>=2.0.0",
        "rapidfuzz>=3.0.0",
        "tqdm>=4.66.0",
        "structlog>=23.0.0",
        "tenacity>=8.2.0",
    ],
    extras_require={
        "full": [
            "camelot-py[base]>=0.11.0",
            "pdf2doi>=1.5",
            "pymupdf4llm>=0.0.4",
            "opencv-python>=4.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "lenr-collect=lenr_collection.main:main",
        ],
    },
)
