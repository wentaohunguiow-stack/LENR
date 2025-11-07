#!/usr/bin/env python3
"""
Utility script for querying the LENR database
"""

import argparse
from lenr_collection.database import LENRDatabase


def main():
    parser = argparse.ArgumentParser(description="Query LENR paper database")
    parser.add_argument('--db', default='lenr_papers.xlsx', help='Database file path')
    parser.add_argument('--stats', action='store_true', help='Show database statistics')
    parser.add_argument('--author', type=str, help='Search papers by author')
    parser.add_argument('--title', type=str, help='Search papers by title')
    parser.add_argument('--min-score', type=float, help='Filter by minimum DeepSeek score')
    parser.add_argument('--source', type=str, help='Filter by source (lenr-canr, arxiv)')
    parser.add_argument('--export', type=str, help='Export results to CSV file')

    args = parser.parse_args()

    # Load database
    db = LENRDatabase(args.db)

    if args.stats:
        stats = db.get_statistics()
        print("\n=== Database Statistics ===")
        print(f"Total papers: {stats['total_papers']}")
        print(f"Verified: {stats['verified']}")
        print(f"Pending: {stats['pending']}")
        print(f"Failed: {stats['failed']}")
        print(f"Average score: {stats['avg_score']:.2f}")
        print("\nPapers by source:")
        for source, count in stats['sources'].items():
            print(f"  {source}: {count}")
        return

    # Start with full dataframe
    results = db.df

    # Apply filters
    if args.author:
        results = results[results['Authors'].str.contains(args.author, na=False, case=False)]
        print(f"\nFound {len(results)} papers by author '{args.author}'")

    if args.title:
        results = results[results['Title'].str.contains(args.title, na=False, case=False)]
        print(f"\nFound {len(results)} papers with title containing '{args.title}'")

    if args.min_score is not None:
        results = results[results['DeepSeek_Score'] >= args.min_score]
        print(f"\nFound {len(results)} papers with score >= {args.min_score}")

    if args.source:
        results = results[results['Source'] == args.source]
        print(f"\nFound {len(results)} papers from source '{args.source}'")

    # Display results
    if len(results) > 0:
        print("\n=== Results ===")
        for idx, row in results.iterrows():
            print(f"\nTitle: {row['Title']}")
            print(f"Authors: {row['Authors']}")
            print(f"Source: {row['Source']}")
            print(f"Date: {row['Date_Published']}")
            print(f"Score: {row['DeepSeek_Score']:.2f}")
            print(f"URL: {row['URL']}")
            if row['DeepSeek_Summary']:
                print(f"Summary: {row['DeepSeek_Summary'][:200]}...")
            print("-" * 80)

        # Export if requested
        if args.export:
            results.to_csv(args.export, index=False)
            print(f"\nExported {len(results)} papers to {args.export}")
    else:
        print("\nNo results found.")


if __name__ == "__main__":
    main()
