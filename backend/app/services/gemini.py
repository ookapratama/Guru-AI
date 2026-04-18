"""
Service untuk Prompt Engineering dan Integrasi Google Gemini API.
Menangani pembuatan "Super Prompt" dan pemanggilan model multimodal.

Modul ini berisi dua fungsi utama:
- build_prompt(): Merakit prompt terstruktur untuk Gemini
- call_gemini(): Memanggil Gemini API (teks + gambar) dan parse hasilnya

Menggunakan SDK terbaru: google-genai (pengganti google-generativeai yang deprecated)
"""
import json
import base64
import re
from io import BytesIO
from typing import Optional, List

from google import genai
from google.genai import types
from PIL import Image

from app.core.config import settings

# Inisialisasi client Gemini dengan API key
client = genai.Client(api_key=settings.GOOGLE_API_KEY)

# Nama model yang digunakan
MODEL_NAME = "gemini-2.0-flash"


def build_prompt(
    query_text: str,
    context_docs: List[str],
    subject: Optional[str] = None,
) -> str:
    """
    Merakit "Super Prompt" yang menggabungkan:
    - System instruction: peran sebagai tutor akademik SMA
    - Context block: dokumen relevan dari RAG (Langkah 2)
    - User input: pertanyaan + mata pelajaran

    Args:
        query_text: Pertanyaan/instruksi dari user.
        context_docs: Daftar teks dokumen relevan dari retrieval.
        subject: Mata pelajaran (opsional).

    Returns:
        String prompt lengkap yang siap dikirim ke Gemini.
    """

    # Gabungkan dokumen konteks menjadi satu blok teks
    # Jika tidak ada dokumen, beri tahu Gemini agar mengandalkan pengetahuannya
    if context_docs:
        context_block = "\n\n---\n\n".join(
            [f"[Referensi {i+1}]\n{doc}" for i, doc in enumerate(context_docs)]
        )
    else:
        context_block = "(Tidak ada dokumen referensi yang tersedia. Gunakan pengetahuanmu sendiri.)"

    # Tentukan informasi mata pelajaran
    subject_info = f"Mata pelajaran: **{subject}**" if subject else "Mata pelajaran: Tidak ditentukan (deteksi otomatis dari soal)"

    # Rakit Super Prompt
    prompt = f"""## SYSTEM INSTRUCTION

Kamu adalah **EduSolve AI**, seorang tutor akademik SMA yang sabar, sistematis, dan sangat kompeten.
Tugasmu adalah menyelesaikan soal yang diberikan oleh siswa dengan langkah-langkah yang jelas dan mudah dipahami.

### Aturan Wajib:
1. **Identifikasi konsep** — Tentukan topik/konsep akademik dari soal tersebut.
2. **Jelaskan step-by-step** — Berikan langkah penyelesaian yang detail, runtut, dan mudah dipahami oleh siswa SMA. Gunakan format markdown.
3. **Berikan jawaban akhir** — Tuliskan jawaban final yang ringkas dan to-the-point.
4. **Gunakan referensi** — Jika ada dokumen referensi yang relevan, gunakan sebagai dasar penjelasanmu.
5. **Bahasa Indonesia** — Seluruh penjelasan WAJIB dalam Bahasa Indonesia.
6. **Format LaTeX** — Gunakan notasi LaTeX (misal: `$x^2$`, `$\\frac{{a}}{{b}}$`) untuk rumus matematika.

---

## DOKUMEN REFERENSI (RAG Context)

{context_block}

---

## INPUT SISWA

{subject_info}

**Pertanyaan/Instruksi:**
{query_text}

---

## FORMAT OUTPUT

Balas HANYA dalam format JSON valid dengan struktur berikut (tanpa markdown code block, murni JSON saja):

{{
    "concept": "Nama konsep/topik akademik yang terdeteksi dari soal",
    "steps": "Langkah-langkah penyelesaian secara detail dalam format markdown. Gunakan **bold**, numbering, dan LaTeX jika perlu.",
    "final_answer": "Jawaban akhir yang ringkas dan jelas"
}}
"""

    return prompt.strip()


async def call_gemini(prompt: str, image_base64: str) -> dict:
    """
    Memanggil Google Gemini API secara multimodal (teks + gambar).

    Args:
        prompt: Super prompt hasil dari build_prompt().
        image_base64: Foto soal dalam format base64 string.

    Returns:
        Dictionary dengan key: concept, steps, final_answer.

    Raises:
        ValueError: Jika response dari Gemini tidak bisa di-parse sebagai JSON.
        Exception: Jika terjadi error saat memanggil Gemini API.
    """

    try:
        # Decode base64 string menjadi objek PIL Image
        # Gemini SDK menerima PIL.Image sebagai input gambar
        image_bytes = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_bytes))

    except Exception as e:
        raise ValueError(
            f"Gagal decode gambar base64. Pastikan format base64 valid. Detail: {str(e)}"
        )

    try:
        # Kirim prompt (teks) + gambar ke Gemini secara multimodal
        # Menggunakan SDK google-genai yang baru (pengganti google-generativeai)
        response = await client.aio.models.generate_content(
            model=MODEL_NAME,
            contents=[image, prompt],
            config=types.GenerateContentConfig(
                temperature=0.3,           # Rendah agar jawaban konsisten & akurat
                top_p=0.95,
                max_output_tokens=4096,    # Cukup untuk penjelasan detail
                response_mime_type="application/json",  # Paksa output JSON
            ),
        )

        # Ambil teks response dari Gemini
        raw_text = response.text.strip()

    except Exception as e:
        raise Exception(
            f"Gagal memanggil Gemini API. Pastikan API key valid dan kuota tersedia. Detail: {str(e)}"
        )

    # Parse response JSON dari Gemini
    try:
        # Bersihkan jika Gemini membungkus dengan markdown code block
        cleaned = _clean_json_response(raw_text)
        result = json.loads(cleaned)

        # Validasi bahwa key yang dibutuhkan ada
        required_keys = ["concept", "steps", "final_answer"]
        missing_keys = [k for k in required_keys if k not in result]

        if missing_keys:
            raise ValueError(
                f"Response Gemini tidak memiliki key yang dibutuhkan: {missing_keys}. "
                f"Response mentah: {raw_text[:500]}"
            )

        return {
            "concept": str(result["concept"]),
            "steps": str(result["steps"]),
            "final_answer": str(result["final_answer"]),
        }

    except json.JSONDecodeError as e:
        raise ValueError(
            f"Response Gemini bukan JSON valid. "
            f"Detail parse error: {str(e)}. "
            f"Response mentah: {raw_text[:500]}"
        )


def _clean_json_response(raw_text: str) -> str:
    """
    Membersihkan response Gemini dari markdown code block jika ada.

    Gemini kadang membungkus JSON dalam ```json ... ``` meskipun
    sudah di-set response_mime_type. Fungsi ini menghandle kasus tersebut.
    """
    # Hapus markdown code block jika ada (```json ... ``` atau ``` ... ```)
    pattern = r"```(?:json)?\s*\n?(.*?)\n?\s*```"
    match = re.search(pattern, raw_text, re.DOTALL)

    if match:
        return match.group(1).strip()

    return raw_text.strip()


async def extract_text_from_file_ocr(file_bytes: bytes, mime_type: str) -> str:
    """
    Mengekstrak teks (OCR) dari file (PDF/Image) menggunakan Gemini 1.5 Flash.
    """
    try:
        prompt = "Ekstrak seluruh teks dan informasi yang ada di dalam dokumen ini. " \
                 "Pertahankan struktur semantik aslinya. " \
                 "Jika ada rumus matematika, tulis menggunakan notasi LaTeX ($...$ atau $$...$$). " \
                 "JANGAN menambahkan teks narasi pembuka, penutup, atau komentar apa pun dari dirimu, cukup output teks ekstraksinya saja."
        
        response = await client.aio.models.generate_content(
            model=MODEL_NAME,
            contents=[
                types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
                prompt
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,  # temperature rendah agar faktual & akurat
            ),
        )
        return response.text.strip()
    except Exception as e:
        raise Exception(f"Gagal melakukan OCR dokumen via Gemini: {str(e)}")

