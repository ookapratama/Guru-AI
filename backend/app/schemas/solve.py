"""
Schemas untuk endpoint /solve.
Mendefinisikan kontrak API antara Frontend dan Backend.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID, uuid4


class SolveRequest(BaseModel):
    """
    Request body dari Frontend ketika user mengirim soal untuk diselesaikan.
    Mendukung input multimodal: gambar (base64) + teks.
    """

    # Foto soal yang diupload user, di-encode dalam format base64
    image_base64: str = Field(
        ...,
        description="Foto soal yang diupload user, di-encode base64.",
        examples=["iVBORw0KGgoAAAANSUhEUg..."]
    )

    # Pertanyaan atau instruksi tambahan dari user
    query_text: str = Field(
        ...,
        description="Pertanyaan atau instruksi tambahan dari user.",
        examples=["Jelaskan langkah-langkah penyelesaian soal ini."]
    )

    # Mata pelajaran (opsional) — membantu Gemini memberikan konteks lebih tepat
    subject: Optional[str] = Field(
        default=None,
        description="Mata pelajaran, contoh: 'matematika', 'fisika', 'bahasa_indonesia'.",
        examples=["matematika", "fisika", "bahasa_indonesia"]
    )


class SolveResponse(BaseModel):
    """
    Response body yang dikirim ke Frontend setelah soal berhasil diproses.
    Berisi hasil analisis AI secara terstruktur.
    """

    # Status proses: "success" atau "error"
    status: str = Field(
        ...,
        description="Status proses: 'success' atau 'error'.",
        examples=["success"]
    )

    # ID unik untuk sesi/pertanyaan ini — berguna untuk tracking & history
    question_id: UUID = Field(
        default_factory=uuid4,
        description="ID unik sesi pertanyaan ini."
    )

    # Konsep/topik akademik yang terdeteksi dari soal
    concept: str = Field(
        ...,
        description="Konsep atau topik akademik yang terdeteksi dari soal.",
        examples=["Turunan Fungsi Aljabar"]
    )

    # Langkah-langkah penyelesaian secara detail (format markdown)
    steps: str = Field(
        ...,
        description="Langkah-langkah penyelesaian soal secara detail.",
        examples=["**Langkah 1:** Identifikasi fungsi f(x) = x² + 3x\n**Langkah 2:** Turunkan..."]
    )

    # Jawaban akhir yang ringkas dan to-the-point
    final_answer: str = Field(
        ...,
        description="Jawaban akhir yang ringkas.",
        examples=["f'(x) = 2x + 3"]
    )

    # Daftar judul/cuplikan dokumen referensi yang digunakan dari RAG
    references_used: List[str] = Field(
        default_factory=list,
        description="Judul atau cuplikan dokumen referensi dari database RAG.",
        examples=[["Bab 4: Turunan — Matematika Wajib Kelas XII", "Modul UTBK Matematika 2024"]]
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "status": "success",
                    "question_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                    "concept": "Turunan Fungsi Aljabar",
                    "steps": "**Langkah 1:** Identifikasi f(x) = x² + 3x\n**Langkah 2:** Gunakan rumus turunan f'(x) = nx^(n-1)\n**Langkah 3:** f'(x) = 2x + 3",
                    "final_answer": "f'(x) = 2x + 3",
                    "references_used": [
                        "Bab 4: Turunan — Matematika Wajib Kelas XII",
                        "Modul UTBK Matematika 2024"
                    ]
                }
            ]
        }
    }
