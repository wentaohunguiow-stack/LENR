# Quick Start Guide

Get started with the LENR Research Collection System in 5 minutes!

## 1. Install Dependencies

```bash
# Create virtual environment
python -m venv lenr_env
source lenr_env/bin/activate  # Windows: lenr_env\Scripts\activate

# Install packages
pip install -r requirements.txt
```

## 2. Configure

Edit `config.json`:

```json
{
    "excel_path": "lenr_papers.xlsx",
    "pdf_dir": "pdfs",
    "deepseek_api_key": "your-api-key-here",
    "sources": ["lenr-canr"],
    "max_papers_per_run": 10
}
```

Optional: Get a DeepSeek API key at https://platform.deepseek.com/

## 3. Run Collection

```bash
python run_collection.py
```

That's it! The system will:
- Scrape LENR-CANR.org
- Download 10 papers
- Extract metadata
- Verify with DeepSeek (if API key provided)
- Save to `lenr_papers.xlsx`

## 4. Query Database

```bash
# Show statistics
python query_db.py --stats

# Find papers by author
python query_db.py --author "Storms"

# Export results
python query_db.py --min-score 0.8 --export results.csv
```

## Next Steps

- Read the full [README.md](README.md) for advanced usage
- Try the [example_usage.ipynb](example_usage.ipynb) notebook
- Increase `max_papers_per_run` in config.json
- Add arXiv source: `"sources": ["lenr-canr", "arxiv"]`

## Common Issues

**"DeepSeek API key not configured"**
- This is fine! The system works without DeepSeek
- Papers will be collected but not verified
- Add API key later to verify existing papers

**"Ghostscript not found"**
- Only needed for table extraction
- Install: `sudo apt-get install ghostscript` (Ubuntu)
- System works without it for basic functionality

**Rate limiting**
- The system is intentionally slow (respectful scraping)
- ~6 papers per minute with 10-second delays
- This is normal and expected

## Support

Issues? Check:
1. [README.md](README.md) - Full documentation
2. [GitHub Issues](https://github.com/yourusername/lenr-collection/issues)
3. Logs at `logs/lenr_collection.log`
