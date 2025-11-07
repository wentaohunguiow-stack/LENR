"""
Database management for LENR papers with duplicate detection
"""

import pandas as pd
import hashlib
from pathlib import Path
from typing import Optional, List, Dict
import logging
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

# Define the optimal schema
LENR_SCHEMA = {
    'Title': str,              # Paper title
    'Authors': str,            # Comma-separated author list
    'URL': str,                # Source URL
    'PDF_Path': str,           # Local filesystem path
    'PDF_Hash': str,           # SHA256 hash for duplicate detection
    'Date_Published': str,     # Publication date (YYYY-MM-DD)
    'Date_Added': str,         # When added to database
    'Journal': str,            # Publication venue
    'Source': str,             # LENR-CANR, arXiv, JCMNS, etc.
    'Verified': bool,          # DeepSeek verification complete
    'DeepSeek_Score': float,   # Relevance score (0-1)
    'DeepSeek_Summary': str,   # AI-generated summary
    'Abstract': str,           # Paper abstract
    'Keywords': str,           # Comma-separated keywords
    'DOI': str,                # Digital Object Identifier
    'Status': str,             # 'pending', 'processed', 'failed'
    'Recnum': str              # Record number from source
}

def create_lenr_database():
    """Initialize LENR paper database"""
    df = pd.DataFrame(columns=LENR_SCHEMA.keys())
    # Set proper dtypes
    for col, dtype in LENR_SCHEMA.items():
        if dtype == str:
            df[col] = df[col].astype('object')
        elif dtype == bool:
            df[col] = df[col].astype('bool')
        elif dtype == float:
            df[col] = df[col].astype('float64')
    return df


class LENRDatabase:
    """Manages LENR paper database with duplicate detection"""

    def __init__(self, excel_path: str = "lenr_papers.xlsx"):
        self.excel_path = Path(excel_path)
        self.df = self._load_or_create()

        # Create indices for fast lookup
        self.url_index = set(self.df['URL'].dropna())
        self.hash_index = set(self.df['PDF_Hash'].dropna())

    def _load_or_create(self) -> pd.DataFrame:
        """Load existing database or create new one"""
        if self.excel_path.exists():
            try:
                df = pd.read_excel(self.excel_path, engine='openpyxl')
                logger.info(f"Loaded {len(df)} existing records")
                return df
            except Exception as e:
                logger.error(f"Failed to load Excel: {e}")
                return create_lenr_database()
        else:
            logger.info("Creating new database")
            return create_lenr_database()

    def compute_pdf_hash(self, pdf_path: str) -> str:
        """Compute SHA256 hash of PDF file"""
        sha256 = hashlib.sha256()
        with open(pdf_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def compute_url_hash(self, url: str) -> str:
        """Normalize and hash URL"""
        # Normalize URL (remove trailing slashes, convert to lowercase)
        normalized = url.rstrip('/').lower()
        return hashlib.md5(normalized.encode()).hexdigest()

    def is_duplicate_url(self, url: str) -> bool:
        """Check if URL already exists (fast O(1) lookup)"""
        return url in self.url_index

    def is_duplicate_pdf(self, pdf_path: str) -> bool:
        """Check if PDF content already exists"""
        if not Path(pdf_path).exists():
            return False

        pdf_hash = self.compute_pdf_hash(pdf_path)
        return pdf_hash in self.hash_index

    def find_similar_titles(self, title: str, threshold: int = 85) -> List[Dict]:
        """Find similar titles using fuzzy matching

        Args:
            title: Title to search for
            threshold: Similarity threshold (0-100), default 85%

        Returns:
            List of similar papers with similarity scores
        """
        if self.df.empty or title is None:
            return []

        similar = []
        for idx, row in self.df.iterrows():
            if pd.isna(row['Title']):
                continue

            similarity = fuzz.ratio(title.lower(), row['Title'].lower())
            if similarity >= threshold:
                similar.append({
                    'title': row['Title'],
                    'url': row['URL'],
                    'similarity': similarity
                })

        return sorted(similar, key=lambda x: x['similarity'], reverse=True)

    def add_paper(self, paper_data: Dict) -> bool:
        """Add paper to database with duplicate checking

        Args:
            paper_data: Dictionary with paper metadata

        Returns:
            True if added, False if duplicate
        """
        # Check URL duplicate (fast)
        if self.is_duplicate_url(paper_data.get('URL', '')):
            logger.info(f"Duplicate URL: {paper_data['URL']}")
            return False

        # Check title similarity (slower, but catches near-duplicates)
        similar = self.find_similar_titles(paper_data.get('Title', ''))
        if similar and similar[0]['similarity'] > 90:
            logger.info(f"Similar title found: {similar[0]['title']} "
                       f"(similarity: {similar[0]['similarity']}%)")
            return False

        # Add to DataFrame
        new_row = pd.DataFrame([paper_data])
        self.df = pd.concat([self.df, new_row], ignore_index=True)

        # Update indices
        self.url_index.add(paper_data.get('URL', ''))
        if paper_data.get('PDF_Hash'):
            self.hash_index.add(paper_data['PDF_Hash'])

        logger.info(f"Added: {paper_data.get('Title', 'Unknown')}")
        return True

    def update_paper(self, url: str, updates: Dict):
        """Update existing paper record"""
        mask = self.df['URL'] == url
        if mask.any():
            for key, value in updates.items():
                self.df.loc[mask, key] = value
            logger.info(f"Updated: {url}")

    def save(self, backup: bool = True):
        """Save database to Excel with optional backup"""
        if backup and self.excel_path.exists():
            backup_path = self.excel_path.with_suffix('.backup.xlsx')
            self.excel_path.rename(backup_path)
            logger.info(f"Backup created: {backup_path}")

        try:
            self.df.to_excel(self.excel_path, index=False, engine='openpyxl')
            logger.info(f"Saved {len(self.df)} records to {self.excel_path}")
        except Exception as e:
            logger.error(f"Failed to save: {e}")
            raise

    def get_pending_papers(self) -> pd.DataFrame:
        """Get papers that need processing"""
        return self.df[self.df['Status'] == 'pending']

    def get_statistics(self) -> Dict:
        """Get database statistics"""
        return {
            'total_papers': len(self.df),
            'verified': len(self.df[self.df['Verified'] == True]),
            'pending': len(self.df[self.df['Status'] == 'pending']),
            'failed': len(self.df[self.df['Status'] == 'failed']),
            'sources': self.df['Source'].value_counts().to_dict() if not self.df.empty else {},
            'avg_score': self.df['DeepSeek_Score'].mean() if not self.df.empty else 0.0
        }


def batch_check_duplicates(database: LENRDatabase,
                          new_papers: List[Dict]) -> List[Dict]:
    """Efficiently check list of papers for duplicates

    Returns:
        List of papers that are not duplicates
    """
    unique_papers = []

    # Convert to DataFrame for vectorized operations
    new_df = pd.DataFrame(new_papers)

    # Fast URL check using set operations
    existing_urls = set(database.df['URL'].dropna())
    new_df['is_duplicate'] = new_df['URL'].isin(existing_urls)

    # Keep only non-duplicates
    non_duplicate_df = new_df[~new_df['is_duplicate']]

    # Additional fuzzy title matching for non-duplicates
    for _, row in non_duplicate_df.iterrows():
        similar = database.find_similar_titles(row['Title'], threshold=90)
        if not similar:
            unique_papers.append(row.to_dict())

    logger.info(f"Found {len(unique_papers)} unique papers out of {len(new_papers)}")
    return unique_papers
