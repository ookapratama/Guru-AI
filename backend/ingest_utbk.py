#!/usr/bin/env python
"""
CLI Script untuk UTBK PDF Ingestion dengan Gemini Vision OCR.
Extract soal-soal dari PDF, gunakan Gemini Vision untuk OCR + metadata, embed & upload ke Supabase.

Usage:
    docker-compose exec api python ingest_utbk.py [--pdf-dir /app/data]

Requirements:
- PDF files di /app/data/ (atau custom --pdf-dir)
- GOOGLE_API_KEY di .env (untuk Gemini Vision)
- SUPABASE credentials di .env
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.ingest_utbk import ingest_pdf_utbk_pipeline


def main():
    """Main entry point untuk UTBK ingest CLI."""
    parser = argparse.ArgumentParser(
        description="UTBK PDF Ingestion CLI - Gemini Vision OCR + metadata extraction"
    )
    parser.add_argument(
        "--pdf-dir",
        type=str,
        default="/app/data",
        help="Direktori yang berisi file-file PDF (default: /app/data)"
    )
    
    args = parser.parse_args()
    
    # Run pipeline
    result = ingest_pdf_utbk_pipeline(pdf_dir=args.pdf_dir)
    
    # Print summary
    print("\n" + "=" * 70)
    if result["success"]:
        print(f"✓ SUCCESS: {result['message']}")
    else:
        print(f"✗ FAILED: {result['message']}")
    
    stats = result["stats"]
    print(f"\nStatistics:")
    print(f"  • PDF Files: {stats['pdf_files']}")
    print(f"  • Soal Extracted: {stats['soal_count']}")
    print(f"  • Soal Uploaded: {stats['uploaded']}")
    print("=" * 70)
    
    # Exit code
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
