#!/usr/bin/env python
"""
Debug script untuk check PDF content extraction.
Lihat apakah pages berhasil di-extract textnya atau kosong.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from langchain_community.document_loaders import PyPDFLoader

def debug_pdf_content(data_dir: str = "/app/data"):
    """Check content dari setiap PDF page."""
    
    pdf_files = list(Path(data_dir).glob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {data_dir}")
        return
    
    print(f"Found {len(pdf_files)} PDF file(s)\n")
    
    for pdf_file in pdf_files:
        print(f"📄 {pdf_file.name}")
        print("-" * 60)
        
        try:
            loader = PyPDFLoader(str(pdf_file))
            documents = loader.load()
            
            print(f"  Total pages: {len(documents)}")
            
            # Check content
            empty_pages = 0
            non_empty_pages = 0
            
            for i, doc in enumerate(documents):
                content_length = len(doc.page_content.strip())
                page_num = doc.metadata.get('page', i)
                
                if content_length == 0:
                    empty_pages += 1
                    print(f"  Page {page_num}: ❌ EMPTY (0 chars)")
                else:
                    non_empty_pages += 1
                    preview = doc.page_content[:100].replace('\n', ' ')
                    print(f"  Page {page_num}: ✓ {content_length} chars → {preview}...")
            
            print(f"\n  Summary: {non_empty_pages} pages with content, {empty_pages} empty pages")
            
        except Exception as e:
            print(f"  ERROR: {str(e)}")
        
        print()

if __name__ == "__main__":
    debug_pdf_content()