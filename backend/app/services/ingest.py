"""
Service untuk PDF Ingestion → Vector Embeddings → Supabase.
Modul ini berisi core logic untuk membaca PDF, split chunks, generate embeddings,
dan upload ke Supabase. Bisa digunakan baik sebagai service di FastAPI atau
CLI script standalone.

Core Functions:
- load_pdfs_from_directory()
- split_documents()
- ingest_chunks_to_supabase()
"""

import os
from pathlib import Path
from typing import List, Tuple
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import httpx
from langchain_core.documents import Document

from app.core.config import settings
from app.db.supabase import supabase_client
from app.services.groq_service import extract_text_from_file_ocr_groq


# ============================================================
# CONFIGURATION
# ============================================================

CHUNK_SIZE: int = 1000
CHUNK_OVERLAP: int = 100
EMBEDDING_MODEL: str = "models/text-embedding-004"
VECTOR_STORE_TABLE: str = "documents"


# ============================================================
# CORE FUNCTIONS
# ============================================================

def load_pdfs_from_directory(data_dir: str) -> List[Document]:
    """
    Membaca semua file .pdf dari direktori yang diberikan.

    Args:
        data_dir: Path ke direktori yang berisi file-file PDF.

    Returns:
        List berisi Document objects dari semua PDF.
        Jika tidak ada PDF, return list kosong.

    Raises:
        FileNotFoundError: Jika direktori tidak ada.
    """
    if not os.path.exists(data_dir):
        raise FileNotFoundError(f"Direktori tidak ditemukan: {data_dir}")
    
    pdf_files = list(Path(data_dir).glob("*.pdf"))
    
    if not pdf_files:
        return []
    
    print(f"[INFO] Ditemukan {len(pdf_files)} file PDF")
    
    all_documents: List[Document] = []
    
    for pdf_file in pdf_files:
        try:
            print(f"[PROCESSING] {pdf_file.name}...")
            loader = PyPDFLoader(str(pdf_file))
            documents = loader.load()
            
            # Tambahkan metadata source
            for doc in documents:
                doc.metadata["source_file"] = pdf_file.name
            
            all_documents.extend(documents)
            print(f"  ✓ {len(documents)} pages")
            
        except Exception as e:
            print(f"[ERROR] {pdf_file.name}: {str(e)}")
            continue
    
    print(f"[INFO] Total {len(all_documents)} pages")
    return all_documents


def split_documents(
    documents: List[Document],
    chunk_size: int = CHUNK_SIZE,
    chunk_overlap: int = CHUNK_OVERLAP,
) -> List[Document]:
    """
    Split documents menjadi chunks.

    Args:
        documents: List of Document objects.
        chunk_size: Ukuran chunk (default: 1000).
        chunk_overlap: Overlap antar chunks (default: 100).

    Returns:
        List berisi Document chunks.
    """
    if not documents:
        return []
    
    print(f"[INFO] Splitting dengan chunk_size={chunk_size}, overlap={chunk_overlap}...")
    
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", " ", ""],
    )
    
    chunks = splitter.split_documents(documents)
    print(f"[INFO] Total {len(chunks)} chunks")
    
    return chunks


async def get_hf_embeddings_async(texts: List[str]) -> List[List[float]]:
    """Native request ke HuggingFace agar terhindar dari bug JSONDecodeError LangChain."""
    import httpx
    # Rute terbaru HuggingFace API menggunaan sistem router. all-mpnet-base-v2 dipilih karena memproduksi 768 dimensi vektor.
    api_url = "https://router.huggingface.co/hf-inference/models/sentence-transformers/all-mpnet-base-v2/pipeline/feature-extraction"
    headers = {"Authorization": f"Bearer {settings.HF_TOKEN}"}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(api_url, headers=headers, json={"inputs": texts, "options": {"wait_for_model": True}})
        
        if response.status_code != 200:
            raise ValueError(f"HTTP {response.status_code}: {response.text}")
            
        data = response.json()
        if not isinstance(data, list):
             raise ValueError(f"Respon tidak valid dari HF: {data}")
        return data


async def ingest_chunks_to_supabase(
    chunks: List[Document],
    table_name: str = VECTOR_STORE_TABLE,
) -> Tuple[int, str]:
    """
    Upload document chunks ke Supabase sebagai embeddings.

    Args:
        chunks: List of Document chunks.
        table_name: Nama tabel di Supabase (default: "documents").

    Returns:
        Tuple (count_uploaded, status_message).

    Raises:
        ValueError: Jika chunks kosong atau ada error.
    """
    if not chunks:
        raise ValueError("Tidak ada chunks untuk di-upload")
    
    if supabase_client is None:
        raise ValueError("Supabase client tidak aktif. Cek .env SUPABASE_URL dan SUPABASE_KEY")
    
    try:
        print(f"[INFO] Uploading {len(chunks)} chunks ke Supabase tabel '{table_name}'...")
        
        # 1. Generate Embeddings text (Custom HTTP Request)
        texts = [doc.page_content for doc in chunks]
        print("[INFO] Generating vectors via Native HF Pipeline...")
        embedded_vectors = await get_hf_embeddings_async(texts)
        
        # 2. Map data sesuai skema database asli (context, metadata, embedding)
        data_to_insert = []
        for chunk, vector in zip(chunks, embedded_vectors):
            data_to_insert.append({
                "content": chunk.page_content,
                "metadata": chunk.metadata,
                "embedding": vector
            })
            
        # 3. Eksekusi native Supabase python client
        print(f"[INFO] Menyuntikkan matriks ke dalam Database...")
        response = supabase_client.table(table_name).insert(data_to_insert).execute()
        
        message = f"Berhasil upload {len(chunks)} row data ke tabel Supabase '{table_name}'"
        print(f"[SUCCESS] {message}")
        return len(chunks), message
        
    except Exception as e:
        error_msg = f"Gagal ingest ke Supabase (Kemungkinan HF_TOKEN salah atau Kolom/Tabel tidak sesuai): {str(e)}"
        print(f"[ERROR] {error_msg}")
        raise ValueError(error_msg)


async def ingest_pdf_pipeline(data_dir: str) -> dict:
    """
    Pipeline lengkap: Load → Split → Ingest.
    Bisa digunakan dari FastAPI endpoint atau CLI.

    Args:
        data_dir: Path ke direktori PDF.

    Returns:
        dict dengan status dan statistics.
    """
    try:
        # Load
        print(f"\n[STEP 1] Load PDFs dari {data_dir}...")
        documents = load_pdfs_from_directory(data_dir)
        
        if not documents:
            return {
                "success": False,
                "message": f"Tidak ada PDF ditemukan di {data_dir}",
                "stats": {"documents": 0, "chunks": 0, "uploaded": 0}
            }
        
        # Split
        print(f"\n[STEP 2] Split documents...")
        chunks = split_documents(documents)
        
        if not chunks:
            return {
                "success": False,
                "message": "Tidak ada chunks yang dihasilkan",
                "stats": {"documents": len(documents), "chunks": 0, "uploaded": 0}
            }
        
        # Ingest
        print(f"\n[STEP 3] Ingest to Supabase...")
        uploaded, msg = await ingest_chunks_to_supabase(chunks)
        
        return {
            "success": True,
            "message": msg,
            "stats": {
                "documents": len(documents),
                "chunks": len(chunks),
                "uploaded": uploaded
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "stats": {"documents": 0, "chunks": 0, "uploaded": 0}
        }


async def process_uploaded_file_ocr(file_bytes: bytes, filename: str, mime_type: str) -> dict:
    """
    Pipeline OCR lengkap untuk satu file upload: 
    Mengekstrak Teks via Llama 3 Groq -> Splitting per chunk -> Ingest to Supabase.
    """
    try:
        print(f"\n[STEP 1] Ekstrak Teks (OCR) dari {filename} menggunakan Groq Llama 3 Vision...")
        extracted_text = await extract_text_from_file_ocr_groq(file_bytes, mime_type)
        
        if not extracted_text:
            return {
                "success": False, 
                "message": "Gagal: Teks hasil OCR kosong.", 
                "filename": filename,
                "stats": {}
            }
            
        print(f"\n[STEP 2] Splitting teks (panjang {len(extracted_text)} karakter)...")
        doc = Document(page_content=extracted_text, metadata={"source_file": filename, "method": "groq_llama_ocr"})
        
        # Split dokumen
        chunks = split_documents([doc])
        
        if not chunks:
             return {
                 "success": False, 
                 "message": "Tidak ada chunks yang dihasilkan setelah proses splitting.", 
                 "filename": filename,
                 "stats": {}
             }
             
        # Ingest
        print(f"\n[STEP 3] Menyimpan vector embeddings ke Supabase...")
        uploaded, msg = await ingest_chunks_to_supabase(chunks)
        
        return {
            "success": True,
            "message": msg,
            "filename": filename,
            "stats": {
                "chars_extracted": len(extracted_text),
                "chunks": len(chunks),
                "uploaded": uploaded
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": str(e),
            "filename": filename,
            "stats": {}
        }
