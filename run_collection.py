#!/usr/bin/env python3
"""
Simple runner script for LENR collection system
"""

import asyncio
import sys
from pathlib import Path

# Ensure logs directory exists
Path("logs").mkdir(exist_ok=True)

from lenr_collection.main import LENRCollectionSystem


async def main():
    """Run the collection system"""
    print("=" * 80)
    print("LENR Research Collection System")
    print("=" * 80)
    print()

    # Check if config exists
    config_path = Path("config.json")
    if not config_path.exists():
        print("ERROR: config.json not found!")
        print("Please create a config.json file based on config.json.template")
        sys.exit(1)

    # Initialize and run system
    try:
        system = LENRCollectionSystem(str(config_path))
        await system.run()
        print("\n✓ Collection completed successfully!")

    except KeyboardInterrupt:
        print("\n\n✗ Collection interrupted by user")
        sys.exit(130)

    except Exception as e:
        print(f"\n✗ Collection failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
