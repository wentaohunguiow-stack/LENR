"""
LENR Research Collection System

An automated system for collecting, processing, and verifying Low Energy Nuclear Reaction research papers.
"""

__version__ = "1.0.0"
__author__ = "LENR Research Team"

from .database import LENRDatabase, LENR_SCHEMA, create_lenr_database
from .scrapers import LENRCANRScraper, ArXivScraper, ScraperConfig
from .downloader import PDFDownloader
from .processor import PDFProcessor
from .verifier import DeepSeekVerifier
from .main import LENRCollectionSystem

__all__ = [
    'LENRDatabase',
    'LENR_SCHEMA',
    'create_lenr_database',
    'LENRCANRScraper',
    'ArXivScraper',
    'ScraperConfig',
    'PDFDownloader',
    'PDFProcessor',
    'DeepSeekVerifier',
    'LENRCollectionSystem'
]
