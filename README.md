# LENR Research Collection System

An automated Python system for collecting, processing, and verifying Low Energy Nuclear Reaction (LENR) research papers. The system combines web scraping, PDF processing, DeepSeek AI verification, and Excel data management to automatically collect papers from multiple sources while intelligently avoiding duplicates.

## Features

- **Multi-Source Scraping**: Collect papers from LENR-CANR.org (2,300+ papers) and arXiv
- **Intelligent Duplicate Detection**: Hash-based exact matching + fuzzy title matching
- **PDF Processing**: Extract metadata, full text, and abstracts using PyMuPDF
- **AI Verification**: Score paper relevance using DeepSeek API (98% cheaper than GPT-4)
- **Robust Error Handling**: Checkpoint-based recovery, exponential backoff, retry logic
- **Respectful Scraping**: Rate limiting (10-15s between requests), proper User-Agent headers
- **Production-Ready**: Comprehensive logging, progress tracking, database backups

## System Architecture

```
lenr_collection/
├── database.py      # Excel database with duplicate detection
├── scrapers.py      # Web scrapers (LENR-CANR, arXiv)
├── downloader.py    # PDF downloader with progress tracking
├── processor.py     # PDF metadata and text extraction
├── verifier.py      # DeepSeek API integration
└── main.py          # Main orchestration system
```

## Installation

### Prerequisites

- Python 3.8 or higher
- Ghostscript (for table extraction)

#### Install Ghostscript

**Ubuntu/Debian:**
```bash
sudo apt-get install ghostscript
```

**macOS:**
```bash
brew install ghostscript
```

**Windows:**
Download from https://ghostscript.com/

### Install Python Dependencies

```bash
# Create virtual environment
python -m venv lenr_env
source lenr_env/bin/activate  # On Windows: lenr_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Or install the package
pip install -e .
```

## Configuration

1. Edit `config.json` with your settings:

```json
{
    "excel_path": "lenr_papers.xlsx",
    "pdf_dir": "pdfs",
    "deepseek_api_key": "sk-your-api-key-here",
    "sources": ["lenr-canr", "arxiv"],
    "max_papers_per_run": 50,
    "scraper_config": {
        "requests_per_second": 0.1,
        "max_retries": 3,
        "timeout": 30,
        "user_agent": "Academic LENR Research Bot - contact@your-email.com"
    }
}
```

2. **Get DeepSeek API Key** (optional but recommended):
   - Sign up at https://platform.deepseek.com/
   - Generate an API key
   - Add to `config.json`

## Usage

### Quick Start

```bash
# Run the collection system
python run_collection.py

# Or use the module directly
python -m lenr_collection.main
```

### System Workflow

1. **Scrape** papers from LENR-CANR and arXiv
2. **Filter** duplicates against existing database
3. **Download** PDFs with progress tracking
4. **Extract** metadata and content from PDFs
5. **Verify** content with DeepSeek AI (if enabled)
6. **Save** to Excel with automatic backups

### Query Database

```bash
# Show statistics
python query_db.py --stats

# Find papers by author
python query_db.py --author "Storms"

# Find papers by title keyword
python query_db.py --title "palladium"

# Filter by DeepSeek score
python query_db.py --min-score 0.8

# Filter by source
python query_db.py --source "arXiv"

# Export results to CSV
python query_db.py --author "Storms" --export results.csv
```

## Database Schema

The Excel database includes the following fields:

| Field | Type | Description |
|-------|------|-------------|
| Title | string | Paper title |
| Authors | string | Comma-separated author list |
| URL | string | Source URL |
| PDF_Path | string | Local filesystem path |
| PDF_Hash | string | SHA256 hash for duplicate detection |
| Date_Published | string | Publication date (YYYY-MM-DD) |
| Date_Added | string | When added to database |
| Journal | string | Publication venue |
| Source | string | LENR-CANR, arXiv, etc. |
| Verified | boolean | DeepSeek verification complete |
| DeepSeek_Score | float | Relevance score (0-1) |
| DeepSeek_Summary | string | AI-generated summary |
| Abstract | string | Paper abstract |
| Keywords | string | Comma-separated keywords |
| DOI | string | Digital Object Identifier |
| Status | string | 'pending', 'processed', 'failed' |

## Advanced Usage

### Python API

```python
from lenr_collection import LENRDatabase, LENRCollectionSystem
import asyncio

# Query database
db = LENRDatabase("lenr_papers.xlsx")

# Get high-scoring papers
high_quality = db.df[db.df['DeepSeek_Score'] > 0.8]

# Find papers by author
storms_papers = db.df[db.df['Authors'].str.contains('Storms', na=False)]

# Get statistics
stats = db.get_statistics()
print(f"Total papers: {stats['total_papers']}")
print(f"Average score: {stats['avg_score']:.2f}")

# Run collection programmatically
async def collect():
    system = LENRCollectionSystem()
    await system.run()

asyncio.run(collect())
```

### Incremental Updates

```python
# Only process recent papers
system = LENRCollectionSystem()
system.config['date_filter'] = '2025-09-19'
await system.run()
```

### Re-verify Existing Papers

```python
from lenr_collection import DeepSeekVerifier, LENRDatabase

db = LENRDatabase()
verifier = DeepSeekVerifier("your-api-key")

unverified = db.df[db.df['Verified'] == False]

for idx, paper in unverified.iterrows():
    result = verifier.verify_content(
        paper['Title'],
        paper['Abstract']
    )

    db.update_paper(paper['URL'], {
        'Verified': True,
        'DeepSeek_Score': result['score']
    })

db.save()
```

## Performance

### Expected Throughput

- **With rate limiting** (respectful): 50-100 papers/hour
- **Without rate limiting** (not recommended): 200-500 papers/hour

### Cost Analysis

- **DeepSeek**: ~$0.001 per paper (1000 papers = $1)
- **GPT-4**: ~$0.10 per paper (1000 papers = $100)
- **Savings**: 98% cost reduction with DeepSeek

### Optimization

For processing 1000+ papers:

- Use multiprocessing for PDF extraction (CPU-bound)
- Maintain async for network I/O (downloads/API calls)
- Enable DeepSeek context caching (reduces costs 90%)
- Process PDFs in batches of 50-100

## Error Recovery

The system implements comprehensive recovery:

- **Checkpoint files**: Track processed URLs for resume capability
- **Database backups**: Created before each save operation
- **Failed paper logging**: Review and retry failed downloads
- **Exponential backoff**: Automatic retry with increasing delays
- **Graceful degradation**: Continue without DeepSeek if API unavailable

### Resume After Interruption

The system automatically resumes from the last checkpoint:

```bash
# If interrupted, simply run again
python run_collection.py
```

## Monitoring

Logs are saved to `logs/lenr_collection.log`

Key metrics to monitor:

- Papers processed per hour
- Average DeepSeek score
- Duplicate detection rate
- Download success rate
- API costs and token usage
- Storage space consumed

## Ethical Considerations

This system respects academic sites:

- Conservative 10-second delays between requests
- Descriptive User-Agent headers
- Honors robots.txt directives
- Avoids peak hours (recommended: 1-8 AM UTC)
- Automatic backoff on errors

**NEVER decrease rate limits below recommended values.**

If blocked, wait 24 hours before retry and consider contacting site administrators.

## Troubleshooting

### Common Issues

**1. Ghostscript not found**
```bash
# Install Ghostscript (see Installation section)
# Verify installation
gs --version
```

**2. DeepSeek API errors**
```bash
# Check API key in config.json
# Verify account has credits
# Check rate limits (max 60 requests/minute)
```

**3. PDF download failures**
```bash
# Check network connection
# Verify PDF URLs are accessible
# Review failed papers in checkpoint.json
```

**4. Excel file locked**
```bash
# Close Excel if open
# Check file permissions
# Remove .backup.xlsx if needed
```

### Debug Mode

Enable verbose logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

Contributions welcome! Areas for improvement:

- Add more LENR sources (JCMNS, ICCF proceedings)
- Improve abstract extraction accuracy
- Add citation network analysis
- Implement web dashboard (Streamlit/Flask)
- Add email notifications for errors

## License

MIT License - see LICENSE file for details

## Citation

If you use this system in your research, please cite:

```
LENR Research Collection System (2025)
https://github.com/yourusername/lenr-collection
```

## Contact

For questions, issues, or contributions:
- GitHub Issues: https://github.com/yourusername/lenr-collection/issues
- Email: your-email@university.edu

## Acknowledgments

- LENR-CANR.org for maintaining the comprehensive LENR library
- arXiv for providing the open API
- DeepSeek for affordable AI verification
- The LENR research community

## Version History

### v1.0.0 (2025-11-07)
- Initial release
- LENR-CANR scraper
- arXiv integration
- DeepSeek verification
- Duplicate detection
- Excel database management
