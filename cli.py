#!/usr/bin/env python3
"""
Simple CLI interface for LENR Collection System
Can be used directly from n8n's Execute Command node
"""

import argparse
import json
import sys
import asyncio
from pathlib import Path

from lenr_collection.database import LENRDatabase
from lenr_collection.scrapers import LENRCANRScraper, ArXivScraper, ScraperConfig
from lenr_collection.downloader import PDFDownloader
from lenr_collection.processor import PDFProcessor
from lenr_collection.verifier import DeepSeekVerifier


def collect_papers(args):
    """Collect papers from sources"""

    async def _collect():
        db = LENRDatabase(args.database)
        downloader = PDFDownloader(args.pdf_dir)
        processor = PDFProcessor()

        verifier = None
        if args.verify and args.api_key:
            verifier = DeepSeekVerifier(args.api_key)

        all_papers = []

        # Collect from sources
        if "lenr-canr" in args.sources:
            scraper = LENRCANRScraper(ScraperConfig())
            papers = await scraper.scrape()
            all_papers.extend(papers)

        if "arxiv" in args.sources:
            scraper = ArXivScraper()
            papers = await scraper.search_lenr_papers(max_results=100)
            all_papers.extend(papers)

        # Filter duplicates
        new_papers = [p for p in all_papers if not db.is_duplicate_url(p.get('URL', ''))]
        new_papers = new_papers[:args.max_papers]

        successful = 0
        failed = 0

        for paper in new_papers:
            try:
                # Download
                pdf_path = downloader.download(paper['URL'], paper['Title'])
                if not pdf_path:
                    failed += 1
                    continue

                # Process
                extracted = processor.process_pdf(str(pdf_path))

                # Update paper
                paper.update({
                    'PDF_Path': str(pdf_path),
                    'PDF_Hash': db.compute_pdf_hash(str(pdf_path)),
                    'Abstract': extracted.get('abstract') or paper.get('Abstract', ''),
                    'Status': 'processed'
                })

                # Verify
                if verifier:
                    verification = verifier.verify_content(
                        paper['Title'],
                        paper.get('Abstract', ''),
                        extracted.get('text', '')[:5000]
                    )
                    paper['Verified'] = True
                    paper['DeepSeek_Score'] = verification['score']
                    paper['DeepSeek_Summary'] = verification['summary']

                # Add to database
                db.add_paper(paper)
                successful += 1

            except Exception as e:
                failed += 1
                if args.verbose:
                    print(f"Error processing {paper.get('Title')}: {e}", file=sys.stderr)

        # Save
        db.save(backup=True)

        # Output JSON result
        result = {
            "success": True,
            "collected": len(new_papers),
            "successful": successful,
            "failed": failed,
            "database": args.database
        }

        print(json.dumps(result, indent=2))

    asyncio.run(_collect())


def query_papers(args):
    """Query papers from database"""
    db = LENRDatabase(args.database)
    results = db.df

    # Apply filters
    if args.author:
        results = results[results['Authors'].str.contains(args.author, na=False, case=False)]

    if args.title:
        results = results[results['Title'].str.contains(args.title, na=False, case=False)]

    if args.min_score is not None:
        results = results[results['DeepSeek_Score'] >= args.min_score]

    if args.source:
        results = results[results['Source'] == args.source]

    # Limit
    results = results.head(args.limit)

    # Output
    if args.output_format == "json":
        papers = results.to_dict('records')
        print(json.dumps({"total": len(papers), "papers": papers}, indent=2))
    elif args.output_format == "csv":
        print(results.to_csv(index=False))
    else:
        for _, row in results.iterrows():
            print(f"Title: {row['Title']}")
            print(f"Authors: {row['Authors']}")
            print(f"Score: {row['DeepSeek_Score']}")
            print(f"URL: {row['URL']}")
            print("-" * 80)


def get_statistics(args):
    """Get database statistics"""
    db = LENRDatabase(args.database)
    stats = db.get_statistics()
    print(json.dumps(stats, indent=2))


def export_database(args):
    """Export database to file"""
    db = LENRDatabase(args.database)

    if args.format == "csv":
        db.df.to_csv(args.output, index=False)
    elif args.format == "json":
        db.df.to_json(args.output, orient='records', indent=2)
    elif args.format == "excel":
        db.df.to_excel(args.output, index=False)

    print(json.dumps({
        "success": True,
        "format": args.format,
        "output": args.output,
        "records": len(db.df)
    }))


def main():
    parser = argparse.ArgumentParser(
        description="LENR Research Collection System CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Collect 10 papers from LENR-CANR
  python cli.py collect --sources lenr-canr --max-papers 10

  # Query papers by author
  python cli.py query --author "Storms" --output-format json

  # Get statistics
  python cli.py stats

  # Export to CSV
  python cli.py export --format csv --output papers.csv
        """
    )

    parser.add_argument('--database', default='lenr_papers.xlsx', help='Database file path')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Collect command
    collect_parser = subparsers.add_parser('collect', help='Collect papers')
    collect_parser.add_argument('--sources', nargs='+', default=['lenr-canr'],
                               choices=['lenr-canr', 'arxiv'], help='Sources to scrape')
    collect_parser.add_argument('--max-papers', type=int, default=10,
                               help='Maximum papers to collect')
    collect_parser.add_argument('--verify', action='store_true',
                               help='Verify with DeepSeek')
    collect_parser.add_argument('--api-key', help='DeepSeek API key')
    collect_parser.add_argument('--pdf-dir', default='pdfs', help='PDF directory')

    # Query command
    query_parser = subparsers.add_parser('query', help='Query papers')
    query_parser.add_argument('--author', help='Filter by author')
    query_parser.add_argument('--title', help='Filter by title')
    query_parser.add_argument('--min-score', type=float, help='Minimum DeepSeek score')
    query_parser.add_argument('--source', help='Filter by source')
    query_parser.add_argument('--limit', type=int, default=100, help='Maximum results')
    query_parser.add_argument('--output-format', choices=['json', 'csv', 'text'],
                             default='json', help='Output format')

    # Stats command
    stats_parser = subparsers.add_parser('stats', help='Get statistics')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export database')
    export_parser.add_argument('--format', choices=['csv', 'json', 'excel'],
                              required=True, help='Export format')
    export_parser.add_argument('--output', required=True, help='Output file')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    try:
        if args.command == 'collect':
            collect_papers(args)
        elif args.command == 'query':
            query_papers(args)
        elif args.command == 'stats':
            get_statistics(args)
        elif args.command == 'export':
            export_database(args)
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
