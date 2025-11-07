"""
PDF downloader with progress tracking and resume capability
"""

import requests
from pathlib import Path
from tqdm import tqdm
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class PDFDownloader:
    """Download PDFs with progress tracking and resume capability"""

    def __init__(self, output_dir: str = "pdfs"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)

    def sanitize_filename(self, filename: str) -> str:
        """Create safe filename from title"""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')

        # Limit length
        return filename[:200]

    def download(self, url: str, title: str,
                max_retries: int = 3) -> Optional[Path]:
        """Download PDF with progress bar and retry logic"""

        filename = self.sanitize_filename(title) + '.pdf'
        filepath = self.output_dir / filename

        # Skip if already exists and valid
        if filepath.exists() and self._validate_pdf(filepath):
            logger.info(f"PDF exists: {filename}")
            return filepath

        for attempt in range(max_retries):
            try:
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()

                total_size = int(response.headers.get('content-length', 0))

                with tqdm(total=total_size, unit='B', unit_scale=True,
                         desc=f"Downloading {filename[:30]}") as pbar:
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            if chunk:
                                f.write(chunk)
                                pbar.update(len(chunk))

                # Validate download
                if self._validate_pdf(filepath):
                    logger.info(f"Downloaded: {filename}")
                    return filepath
                else:
                    logger.error(f"Invalid PDF: {filename}")
                    filepath.unlink()

            except Exception as e:
                logger.error(f"Download failed (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)
                else:
                    return None

        return None

    def _validate_pdf(self, filepath: Path) -> bool:
        """Verify file is valid PDF"""
        try:
            with open(filepath, 'rb') as f:
                header = f.read(4)
                return header == b'%PDF'
        except:
            return False
