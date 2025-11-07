"""
Web scrapers for LENR research sources
"""

import asyncio
import aiohttp
from bs4 import BeautifulSoup
import time
import logging
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ScraperConfig:
    """Configuration for LENR scraper"""
    requests_per_second: float = 0.1  # Very conservative: 1 request per 10 seconds
    max_retries: int = 3
    timeout: int = 30
    user_agent: str = "Academic Research Bot (LENR Study) - contact@university.edu"


class LENRCANRScraper:
    """Scraper for LENR-CANR.org library"""

    def __init__(self, config: ScraperConfig):
        self.config = config
        self.base_url = "https://lenr-canr.org"
        self.session = None
        self.last_request_time = 0

    async def _rate_limit(self):
        """Enforce rate limiting"""
        min_interval = 1.0 / self.config.requests_per_second
        elapsed = time.time() - self.last_request_time

        if elapsed < min_interval:
            await asyncio.sleep(min_interval - elapsed)

        self.last_request_time = time.time()

    async def fetch(self, url: str) -> Optional[str]:
        """Fetch URL with retries and rate limiting"""
        await self._rate_limit()

        for attempt in range(self.config.max_retries):
            try:
                headers = {'User-Agent': self.config.user_agent}
                timeout = aiohttp.ClientTimeout(total=self.config.timeout)

                async with self.session.get(url, headers=headers,
                                           timeout=timeout) as response:
                    response.raise_for_status()

                    logger.info(f"Fetch success: {url} (status={response.status})")
                    return await response.text()

            except Exception as e:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.warning(f"Fetch failed: {url} (attempt {attempt + 1}, "
                             f"error={str(e)}, retry_in={wait_time}s)")

                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Fetch exhausted: {url}")
                    return None

    async def scrape_library_page(self) -> List[Dict]:
        """Scrape LENR-CANR library metadata page"""
        url = f"{self.base_url}/wordpress/?page_id=3009"

        html = await self.fetch(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        papers = []

        # Find table with paper data
        table = soup.find('table')
        if not table:
            logger.error("Parse failed: No table found")
            return []

        rows = table.find_all('tr')[1:]  # Skip header

        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 9:
                continue

            try:
                # Extract PDF link
                pdf_link = None
                link_elem = cells[8].find('a')
                if link_elem:
                    pdf_link = link_elem.get('href')
                    if pdf_link and not pdf_link.startswith('http'):
                        pdf_link = f"{self.base_url}/{pdf_link.lstrip('/')}"

                paper = {
                    'Title': cells[5].text.strip(),
                    'Authors': cells[4].text.strip(),
                    'Date_Published': cells[2].text.strip(),
                    'Journal': cells[6].text.strip() if len(cells) > 6 else '',
                    'URL': pdf_link,
                    'Source': 'LENR-CANR',
                    'Status': 'pending',
                    'Date_Added': time.strftime('%Y-%m-%d'),
                    'Recnum': cells[0].text.strip() if cells else '',
                    'Verified': False,
                    'DeepSeek_Score': 0.0,
                    'DeepSeek_Summary': '',
                    'Abstract': '',
                    'Keywords': '',
                    'DOI': '',
                    'PDF_Path': '',
                    'PDF_Hash': ''
                }

                papers.append(paper)

            except Exception as e:
                logger.error(f"Parse row failed: {e}")
                continue

        logger.info(f"Scrape complete: {len(papers)} papers found")
        return papers

    async def scrape_pdf_directory(self) -> List[str]:
        """Scrape direct PDF directory listing"""
        url = f"{self.base_url}/acrobat/?C=M;O=D"  # Sort by modification date

        html = await self.fetch(url)
        if not html:
            return []

        soup = BeautifulSoup(html, 'html.parser')
        pdf_links = []

        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.endswith('.pdf'):
                full_url = f"{self.base_url}/acrobat/{href}"
                pdf_links.append(full_url)

        logger.info(f"Directory scrape: {len(pdf_links)} PDFs found")
        return pdf_links

    async def scrape(self) -> List[Dict]:
        """Main scraping method"""
        async with aiohttp.ClientSession() as session:
            self.session = session

            # Scrape library metadata (preferred - includes metadata)
            papers = await self.scrape_library_page()

            # Could also scrape PDF directory as fallback
            # pdf_urls = await self.scrape_pdf_directory()

            return papers


class ArXivScraper:
    """Scraper for arXiv LENR papers using official API"""

    def __init__(self):
        self.base_url = "http://export.arxiv.org/api/query"

    async def search_lenr_papers(self, max_results: int = 500) -> List[Dict]:
        """Search arXiv for LENR papers"""
        try:
            import arxiv

            # Configure client with rate limiting (3 seconds per request)
            client = arxiv.Client(
                page_size=100,
                delay_seconds=3,
                num_retries=3
            )

            # Comprehensive LENR search query
            query = '''
            (ti:LENR OR ti:"cold fusion" OR ti:"condensed matter nuclear science"
            OR ti:"low energy nuclear reactions" OR abs:LENR OR abs:"cold fusion")
            AND (cat:nucl-ex OR cat:cond-mat.mtrl-sci OR cat:physics.gen-ph)
            '''

            search = arxiv.Search(
                query=query,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )

            papers = []
            for result in client.results(search):
                paper = {
                    'Title': result.title,
                    'Authors': ', '.join([a.name for a in result.authors]),
                    'Date_Published': result.published.strftime('%Y-%m-%d'),
                    'Journal': 'arXiv',
                    'URL': result.pdf_url,
                    'Source': 'arXiv',
                    'Abstract': result.summary,
                    'Keywords': ', '.join(result.categories),
                    'DOI': result.doi if result.doi else '',
                    'Status': 'pending',
                    'Date_Added': time.strftime('%Y-%m-%d'),
                    'Recnum': '',
                    'Verified': False,
                    'DeepSeek_Score': 0.0,
                    'DeepSeek_Summary': '',
                    'PDF_Path': '',
                    'PDF_Hash': ''
                }
                papers.append(paper)

                await asyncio.sleep(0.5)  # Extra courtesy

            logger.info(f"arXiv search complete: {len(papers)} papers found")
            return papers

        except ImportError:
            logger.error("arxiv package not installed. Install with: pip install arxiv")
            return []
        except Exception as e:
            logger.error(f"arXiv search failed: {e}")
            return []
