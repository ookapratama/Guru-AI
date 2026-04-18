import base64
import fitz  # PyMuPDF
from typing import List
from groq import AsyncGroq
from app.core.config import settings

client = AsyncGroq(api_key=settings.GROQ_API_KEY)
MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"

async def extract_text_from_file_ocr_groq(file_bytes: bytes, mime_type: str) -> str:
    """
    Ekstrak teks/OCR dari file (PDF atau Gambar) menggunakan Groq Llama 3.2 Vision.
    Menerima bytes mentah dan mengubahnya menjadi base64 inline image.
    """
    base64_images = []
    
    # 1. Konversi Tipe File ke urutan Base64 Image(s)
    if mime_type == "application/pdf":
        doc = fitz.open("pdf", file_bytes)
        # Llama 4 Scout di Groq membatasi maksimal 5 gambar per 1 request
        max_pages = min(len(doc), 5) 
        for page_num in range(max_pages):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=150) # Resolusi moderate untuk OCR, menekan penggunaan token
            png_bytes = pix.tobytes("png")
            b64_str = base64.b64encode(png_bytes).decode("utf-8")
            base64_images.append(f"data:image/png;base64,{b64_str}")
        doc.close()
    else:
        # Jika bukan PDF, asumsikan file adalah gambar mentah (image/jpeg, image/png, dll)
        b64_str = base64.b64encode(file_bytes).decode("utf-8")
        base64_images.append(f"data:{mime_type};base64,{b64_str}")

    if not base64_images:
        raise ValueError("Gagal mendapatkan frame referensi visual dari dokumen.")

    # 2. Susun Payload (Content Array) untuk Llama 3 Vision
    prompt_text = (
        "Ekstrak seluruh teks dan informasi yang ada di dalam gambar/dokumen ini. "
        "Pertahankan struktur semantik aslinya serapi mungkin. "
        "Jika ada rumus matematika, fisika, atau simbol akademik, "
        "WAJIB menulisnya menggunakan notasi matematis LaTeX yaitu di dalam tanda ($...$ atau $$...$$). "
        "JANGAN tambahkan narasi pembuka, penutup, atau kesimpulan apapun dari Anda."
    )
    
    # Struktur Array Pydantic ala OpenAI/Groq Vision
    content_list = []
    
    # Masukkan Prompt teks terlebih dahulu
    content_list.append({
        "type": "text",
        "text": prompt_text
    })
    
    # Masukkan seluruh halaman gambar
    for b64 in base64_images:
        content_list.append({
            "type": "image_url",
            "image_url": {
                "url": b64
            }
        })

    # 3. Lakukan Request Async ke Groq Engine
    try:
        chat_completion = await client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": content_list
                }
            ],
            model=MODEL_NAME,
            temperature=0.1,      # Stabil dan sangat deterministik/faktual
            max_tokens=4096       # Batas wajar untuk OCR
        )
        
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        raise Exception(f"Gagal memanggil sistem OCR Llama 3 via Groq: {str(e)}")
