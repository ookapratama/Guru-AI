"""
Enhanced PDF Ingest Service untuk UTBK Soal-Soal menggunakan Gemini Vision API.
Menangani image-based PDF dengan OCR via Gemini, metadata extraction, dan vector embedding.

Features:
- Extract pages dari PDF sebagai images (Pillow)
- OCR + metadata extraction via Gemini 1.5 Vision (1 API call)
- Smart metadata detection (subject, topic, difficulty, type)
- Generate embeddings untuk vector search
- Upload ke Supabase dengan metadata

Benefits:
- No heavy OCR libraries needed (Pillow already included)
- High accuracy via Gemini Vision
- Free tier: 15,000 requests/month
- Auto-detect metadata dari soal
"""

import os
import json
import base64
import io
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

from PIL import Image
from PyPDF2 import PdfReader
from google import genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.documents import Document

from app.core.config import settings
from app.db.supabase import supabase_client


# ============================================================
# CONFIGURATION
# ============================================================

CHUNK_SIZE: int = 1000
CHUNK_OVERLAP: int = 100
EMBEDDING_MODEL: str = "models/text-embedding-004"
VECTOR_STORE_TABLE: str = "documents"
VISION_MODEL: str = "gemini-1.5-flash"

# Initialize Gemini client
genai_client = genai.Client(api_key=settings.GOOGLE_API_KEY)

# OCR Prompt untuk Gemini Vision
OCR_PROMPT = """
Analyze this image of a UTBK exam question. Extract and provide the following in JSON format:

{
  "soal_text": "Complete text of the question/problem",
  "subject": "Math or English",
  "topic": "Specific topic (e.g., Trigonometry, Reading Comprehension, Grammar)",
  "difficulty": "Easy, Medium, or Hard (based on your judgment)",
  "type": "multiple_choice or essay",
  "correct_answer": "The correct answer if visible, or empty string if not clear"
}

Be accurate and precise. If the answer is not visible in the image, leave that field empty.
"""


# ============================================================
# IMAGE EXTRACTION
# ============================================================

def extract_images_from_pdf(pdf_path: str) -> List[Image.Image]:
    """
    Extract semua halaman dari PDF sebagai PIL Image objects.

    Args:
        pdf_path: Path ke file PDF.

    Returns:
        List of PIL Image objects.
    """
    print(f"[INFO] Extract images dari {Path(pdf_path).name}...")
    
    try:
        pdf_reader = PdfReader(pdf_path)
        images: List[Image.Image] = []
        
        for page_idx, page in enumerate(pdf_reader.pages):
            try:
                # Extract images dari page
                if "/XObject" in page["/Resources"]:
                    xObject = page["/Resources"]["/XObject"].get_object()
                    for obj_name in xObject:
                        if xObject[obj_name]["/Subtype"] == "/Image":
                            obj = xObject[obj_name].get_object()
                            data = obj._get_rawdata()
                            
                            if obj["/ColorSpace"] == "/DeviceRGB":
                                mode = "RGB"
                            else:
                                mode = "L"
                            
                            image = Image.frombytes(
                                mode,
                                (int(obj["/Width"]), int(obj["/Height"])),
                                data
                            )
                            images.append(image)
            except Exception as e:
                print(f"  ⚠ Page {page_idx}: Could not extract images - {str(e)}")
                continue
        
        print(f"  ✓ {len(images)} images extracted")
        return images
        
    except Exception as e:
        print(f"[ERROR] Failed to extract images: {str(e)}")
        return []


def image_to_base64(image: Image.Image) -> str:
    """
    Convert PIL Image ke base64 string untuk Gemini API.

    Args:
        image: PIL Image object.

    Returns:
        Base64 encoded string.
    """
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.standard_b64encode(buffer.read()).decode("utf-8")


# ============================================================
# GEMINI VISION API CALLS
# ============================================================

def extract_soal_metadata_via_gemini(image: Image.Image) -> Dict:
    """
    Send image ke Gemini Vision API untuk OCR + metadata extraction.

    Args:
        image: PIL Image object.

    Returns:
        Dictionary dengan soal_text, subject, topic, difficulty, type, correct_answer.
    """
    try:
        # Convert ke base64
        base64_image = image_to_base64(image)
        
        # Send ke Gemini
        message = genai_client.messages.create(
            model=VISION_MODEL,
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64_image,
                            },
                        },
                        {
                            "type": "text",
                            "text": OCR_PROMPT
                        }
                    ],
                }
            ],
        )
        
        # Parse response
        response_text = message.content[0].text
        
        # Extract JSON dari response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = response_text[json_start:json_end]
            result = json.loads(json_str)
            return result
        else:
            print(f"[WARNING] Could not parse Gemini response")
            return {
                "soal_text": "Could not extract soal text",
                "subject": "Unknown",
                "topic": "Unknown",
                "difficulty": "Unknown",
                "type": "Unknown",
                "correct_answer": ""
            }
        
    except Exception as e:
        print(f"[ERROR] Gemini API error: {str(e)}")
        return {
            "soal_text": "",
            "subject": "Unknown",
            "topic": "Unknown",
            "difficulty": "Unknown",
            "type": "Unknown",
            "correct_answer": ""
        }


# ============================================================
# DOCUMENT CREATION & EMBEDDING
# ============================================================

def create_document_from_soal(
    metadata: Dict,
    pdf_file: str,
    page_number: int,
    soal_id: str,
) -> Document:
    """
    Create LangChain Document object dari Gemini extracted metadata.

    Args:
        metadata: Dictionary dari Gemini vision extraction.
        pdf_file: Nama file PDF.
        page_number: Page number.
        soal_id: Unique soal ID.

    Returns:
        LangChain Document object.
    """
    # Combine metadata untuk content
    full_content = f"""
Mata Pelajaran: {metadata.get('subject', 'Unknown')}
Topik: {metadata.get('topic', 'Unknown')}
Tingkat Kesulitan: {metadata.get('difficulty', 'Unknown')}
Tipe Soal: {metadata.get('type', 'Unknown')}

Soal:
{metadata.get('soal_text', 'N/A')}

Jawaban Benar: {metadata.get('correct_answer', 'N/A')}
    """
    
    doc_metadata = {
        "source_file": pdf_file,
        "page_number": page_number,
        "subject": metadata.get('subject', 'Unknown'),
        "topic": metadata.get('topic', 'Unknown'),
        "difficulty": metadata.get('difficulty', 'Unknown'),
        "type": metadata.get('type', 'Unknown'),
        "soal_id": soal_id,
        "correct_answer": metadata.get('correct_answer', ''),
        "extracted_at": datetime.now().isoformat(),
        "extraction_method": "gemini-1.5-vision",
    }
    
    return Document(
        page_content=full_content.strip(),
        metadata=doc_metadata,
    )


# ============================================================
# MAIN PIPELINE
# ============================================================

def ingest_pdf_utbk_pipeline(pdf_dir: str = "/app/data") -> dict:
    """
    Pipeline lengkap untuk ingest UTBK PDF dengan Gemini Vision OCR.

    Args:
        pdf_dir: Direktori PDF files.

    Returns:
        Dictionary dengan status dan statistics.
    """
    try:
        print("\n" + "=" * 70)
        print("EduSolve AI — UTBK PDF Ingestion (Gemini Vision)")
        print("=" * 70)
        
        # Step 1: Find PDF files
        print("\n[STEP 1] Find PDF files...")
        if not os.path.exists(pdf_dir):
            raise FileNotFoundError(f"PDF directory tidak ditemukan: {pdf_dir}")
        
        pdf_files = list(Path(pdf_dir).glob("*.pdf"))
        if not pdf_files:
            raise ValueError(f"Tidak ada PDF files di {pdf_dir}")
        
        print(f"[INFO] Found {len(pdf_files)} PDF file(s)")
        
        # Step 2: Extract & process soal
        print("\n[STEP 2] Extract images and process via Gemini Vision...")
        all_documents: List[Document] = []
        soal_counter = 0
        
        for pdf_file in pdf_files:
            pdf_name = pdf_file.name
            print(f"\n[PROCESSING] {pdf_name}...")
            
            try:
                # Extract images
                images = extract_images_from_pdf(str(pdf_file))
                
                # Process each image via Gemini
                for page_idx, image in enumerate(images):
                    print(f"  [Vision] Page {page_idx}...", end=" ", flush=True)
                    
                    metadata = extract_soal_metadata_via_gemini(image)
                    
                    if metadata.get('soal_text', '').strip():
                        soal_counter += 1
                        soal_id = f"UTBK_{pdf_name.replace('.pdf', '')}_{page_idx}"
                        
                        # Create document
                        doc = create_document_from_soal(
                            metadata=metadata,
                            pdf_file=pdf_name,
                            page_number=page_idx,
                            soal_id=soal_id,
                        )
                        
                        all_documents.append(doc)
                        print(f"✓ {metadata.get('subject')} - {metadata.get('topic')}")
                    else:
                        print(f"⚠ No soal text extracted")
            
            except Exception as e:
                print(f"[ERROR] Failed processing {pdf_name}: {str(e)}")
                continue
        
        if not all_documents:
            return {
                "success": False,
                "message": "Tidak ada soal yang berhasil di-extract",
                "stats": {"pdf_files": len(pdf_files), "soal_count": 0, "uploaded": 0}
            }
        
        # Step 3: Generate embeddings & upload to Supabase
        print(f"\n[STEP 3] Generate embeddings dan upload ke Supabase...")
        
        if supabase_client is None:
            raise ValueError("Supabase client tidak aktif")
        
        print(f"[INFO] Inisialisasi embeddings ({EMBEDDING_MODEL})...")
        embeddings = GoogleGenerativeAIEmbeddings(
            model=EMBEDDING_MODEL,
            google_api_key=settings.GOOGLE_API_KEY,
        )
        
        print(f"[INFO] Uploading {len(all_documents)} soal ke Supabase...")
        vector_store = SupabaseVectorStore.from_documents(
            documents=all_documents,
            embedding=embeddings,
            client=supabase_client,
            table_name=VECTOR_STORE_TABLE,
        )
        
        print(f"[SUCCESS] Berhasil upload {len(all_documents)} soal")
        
        return {
            "success": True,
            "message": f"Berhasil ingest {len(all_documents)} soal UTBK via Gemini Vision",
            "stats": {
                "pdf_files": len(pdf_files),
                "soal_count": len(all_documents),
                "uploaded": len(all_documents),
            }
        }
    
    except Exception as e:
        error_msg = f"Pipeline error: {str(e)}"
        print(f"[ERROR] {error_msg}")
        return {
            "success": False,
            "message": error_msg,
            "stats": {"pdf_files": 0, "soal_count": 0, "uploaded": 0}
        }
