"""
Main orchestration system for LENR paper collection
"""

import asyncio
import logging
from pathlib import Path
import json
from datetime import datetime
from typing import Dict, List

from .database import LENRDatabase
from .scrapers import LENRCANRScraper, ArXivScraper, ScraperConfig
from .downloader import PDFDownloader
from .processor import PDFProcessor
from .verifier import DeepSeekVerifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/lenr_collection.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


class LENRCollectionSystem:
    """Main orchestration system for LENR paper collection"""

    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)

        # Initialize components
        self.database = LENRDatabase(self.config['excel_path'])
        self.downloader = PDFDownloader(self.config['pdf_dir'])
        self.processor = PDFProcessor()

        # Only initialize verifier if API key is provided
        api_key = self.config.get('deepseek_api_key', '')
        if api_key and api_key != 'your-api-key-here':
            self.verifier = DeepSeekVerifier(api_key)
        else:
            self.verifier = None
            logger.warning("DeepSeek API key not configured - verification disabled")

        # Checkpoint file
        self.checkpoint_file = Path("checkpoint.json")
        self.checkpoint = self._load_checkpoint()

    def _load_config(self, path: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(path) as f:
                return json.load(f)
        except FileNotFoundError:
            # Default configuration
            logger.warning(f"Config file not found: {path}, using defaults")
            return {
                'excel_path': 'lenr_papers.xlsx',
                'pdf_dir': 'pdfs',
                'deepseek_api_key': 'your-api-key-here',
                'sources': ['lenr-canr', 'arxiv'],
                'max_papers_per_run': 100
            }

    def _load_checkpoint(self) -> Dict:
        """Load checkpoint from file"""
        if self.checkpoint_file.exists():
            with open(self.checkpoint_file) as f:
                return json.load(f)
        return {'processed': [], 'failed': []}

    def _save_checkpoint(self):
        """Save checkpoint to file"""
        with open(self.checkpoint_file, 'w') as f:
            json.dump(self.checkpoint, f, indent=2)

    async def collect_from_sources(self) -> List[Dict]:
        """Collect papers from all configured sources"""
        all_papers = []

        if 'lenr-canr' in self.config['sources']:
            logger.info("Scraping LENR-CANR.org")
            scraper = LENRCANRScraper(ScraperConfig())
            papers = await scraper.scrape()
            all_papers.extend(papers)
            logger.info(f"Collected {len(papers)} from LENR-CANR")

        if 'arxiv' in self.config['sources']:
            logger.info("Scraping arXiv")
            scraper = ArXivScraper()
            papers = await scraper.search_lenr_papers()
            all_papers.extend(papers)
            logger.info(f"Collected {len(papers)} from arXiv")

        return all_papers

    def filter_new_papers(self, papers: List[Dict]) -> List[Dict]:
        """Filter out duplicates using database"""
        new_papers = []

        for paper in papers:
            url = paper.get('URL', '')
            if not url:
                continue

            if url in self.checkpoint['processed']:
                continue

            if not self.database.is_duplicate_url(url):
                new_papers.append(paper)

        logger.info(f"Found {len(new_papers)} new papers "
                   f"out of {len(papers)} total")
        return new_papers

    async def process_paper(self, paper: Dict) -> bool:
        """Process single paper: download, extract, verify"""
        url = paper.get('URL', '')
        title = paper.get('Title', 'Unknown')

        try:
            # Step 1: Download PDF
            pdf_path = self.downloader.download(url, title)
            if not pdf_path:
                logger.error(f"Download failed: {url}")
                self.checkpoint['failed'].append(url)
                paper['Status'] = 'failed'
                self.database.add_paper(paper)
                return False

            # Step 2: Extract metadata and content
            extracted = self.processor.process_pdf(str(pdf_path))

            # Step 3: Compute PDF hash
            pdf_hash = self.database.compute_pdf_hash(str(pdf_path))

            # Step 4: Update paper data
            paper.update({
                'PDF_Path': str(pdf_path),
                'PDF_Hash': pdf_hash,
                'Abstract': extracted.get('abstract') or paper.get('Abstract', ''),
                'full_text': extracted.get('text', '')[:5000]  # First 5000 chars
            })

            # Step 5: DeepSeek verification (if enabled)
            if self.verifier:
                verification = self.verifier.verify_content(
                    title=title,
                    abstract=paper.get('Abstract', ''),
                    full_text=paper.get('full_text', '')
                )

                paper['Verified'] = True
                paper['DeepSeek_Score'] = verification['score']
                paper['DeepSeek_Summary'] = verification['summary']

                if verification.get('keywords'):
                    paper['Keywords'] = verification['keywords']
            else:
                logger.info("Skipping verification (no API key)")

            paper['Status'] = 'processed'

            # Step 6: Add to database
            self.database.add_paper(paper)

            # Step 7: Update checkpoint
            self.checkpoint['processed'].append(url)
            self._save_checkpoint()

            logger.info(f"Paper processed: {title} (score: {paper.get('DeepSeek_Score', 'N/A')})")
            return True

        except Exception as e:
            logger.error(f"Processing failed: {url} - {e}", exc_info=True)
            self.checkpoint['failed'].append(url)
            paper['Status'] = 'failed'
            self.database.add_paper(paper)
            return False

    async def run(self):
        """Main execution flow"""
        logger.info("=== LENR Collection System Started ===")
        start_time = datetime.now()

        try:
            # Step 1: Collect papers from sources
            logger.info("Step 1: Collecting papers from sources")
            papers = await self.collect_from_sources()

            # Step 2: Filter new papers
            logger.info("Step 2: Filtering for new papers")
            new_papers = self.filter_new_papers(papers)

            # Limit papers per run
            max_papers = self.config.get('max_papers_per_run', 100)
            new_papers = new_papers[:max_papers]

            # Step 3: Process each paper
            logger.info(f"Step 3: Processing {len(new_papers)} papers")

            successful = 0
            failed = 0

            for i, paper in enumerate(new_papers):
                logger.info(f"Processing {i+1}/{len(new_papers)}")

                result = await self.process_paper(paper)

                if result:
                    successful += 1
                else:
                    failed += 1

                # Save database periodically
                if (i + 1) % 10 == 0:
                    self.database.save(backup=True)

            # Step 4: Final save
            logger.info("Step 4: Saving final database")
            self.database.save(backup=True)

            # Step 5: Statistics
            duration = (datetime.now() - start_time).total_seconds()
            stats = self.database.get_statistics()

            logger.info(f"""
=== Collection Complete ===
Duration: {duration:.2f} seconds
Successful: {successful}
Failed: {failed}
Total papers in DB: {stats['total_papers']}
Verified: {stats['verified']}
Average score: {stats['avg_score']:.2f}
Sources: {stats['sources']}
            """)

        except Exception as e:
            logger.error(f"System error: {e}", exc_info=True)
            raise

        finally:
            self._save_checkpoint()


async def main():
    """Main entry point"""
    system = LENRCollectionSystem()
    await system.run()


if __name__ == "__main__":
    asyncio.run(main())
