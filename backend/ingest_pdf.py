#!/usr/bin/env python
"""
CLI Script untuk PDF Ingestion.
Jalankan script ini dari dalam Docker container untuk ingest PDF files.

Usage:
    docker exec guru-ai-api python ingest_pdf.py [--data-dir ./data]

Atau jika di local environment dengan .env setup:
    python backend/ingest_pdf.py
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add backend directory to path agar bisa import app modules
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ingest import ingest_pdf_pipeline


def main():
    """Main entry point untuk CLI."""
    parser = argparse.ArgumentParser(
        description="PDF Ingestion CLI - Load PDFs, generate embeddings, upload to Supabase"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="./data",
        help="Direktori yang berisi file-file PDF (default: ./data)"
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("EduSolve AI — PDF Ingestion Pipeline (CLI)")
    print("=" * 70)
    
    # Run async pipeline
    result = asyncio.run(ingest_pdf_pipeline(args.data_dir))
    
    # Print summary
    print("\n" + "=" * 70)
    if result["success"]:
        print(f"✓ SUCCESS: {result['message']}")
    else:
        print(f"✗ FAILED: {result['message']}")
    
    stats = result["stats"]
    print(f"\nStatistics:")
    print(f"  • PDF Documents: {stats['documents']}")
    print(f"  • Chunks Created: {stats['chunks']}")
    print(f"  • Chunks Uploaded: {stats['uploaded']}")
    print("=" * 70)
    
    # Exit code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
