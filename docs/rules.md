# Engineering Rules & Guidelines

Acuan standar pengodingan untuk memastikan kode tetap clean, readable, dan maintainable.

## 1. General Principles
- **DRY (Don't Repeat Yourself)**: Ekstrak logika berulang ke `services` atau `utils`.
- **KISS (Keep It Simple, Stupid)**: Hindari over-engineering. Solusi sederhana lebih diutamakan.
- **YAGNI (You Ain't Gonna Need It)**: Jangan implementasikan fitur yang belum dibutuhkan oleh PRD.

## 2. Python & FastAPI Standards
- **Type Hints**: Wajib digunakan di setiap fungsi dan variabel.
- **Pydantic Models**: Gunakan Pydantic untuk validasi request dan response body. Hindari mengembalikan dict langsung.
- **Dependency Injection**: Gunakan `Depends()` untuk database session, auth, atau shared services.
- **Docstrings**: Gunakan Google-style docstrings untuk fungsi yang kompleks.

## 3. Database Rules
- **Migrations**: Jangan pernah mengubah database schema secara manual. Gunakan `alembic`.
- **Naming Convention**: Tabel menggunakan snake_case jamak (contoh: `interactions`), kolom menggunakan snake_case tunggal.
- **pgvector**: Pastikan query pencarian vector menggunakan operator `<->` (L2 distance) atau `<=>` (cosine similarity) sesuai kebutuhan.

## 4. AI & Service Rules
- **Gemini Prompts**: Simpan template prompt yang kompleks di file terpisah atau di `app/services/prompts.py`.
- **Error Handling**: Tangkap eksepsi dari API eksternal (Google, Supabase) dan bungkus dalam `HTTPException` yang bermakna.
- **RAG Context**: Pastikan context yang dikirim ke LLM selalu difilter (top k) dan relevan.

## 5. Security
- **Strict CORS**: Hanya izinkan origin dari frontend yang dipercaya.
- **Secret Management**: Jangan pernah hardcode API Key. Selalu gunakan `app/core/config.py`.
