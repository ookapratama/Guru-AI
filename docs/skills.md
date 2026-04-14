# Development Skills & Workflows

Panduan langkah-demi-langkah bagi pengembang (atau AI agent) untuk menyelesaikan tugas-tugas umum.

## ➕ Cara Menambah Endpoint Baru
1. Buat Pydantic schema di `app/schemas/`.
2. Buat logic di `app/services/` (jika ada logic bisnis).
3. Buat router di `app/api/v1/endpoints/`.
4. Register router di `app/api/v1/api.py`.

## 🗄️ Cara Menambah Model Database
1. Definisikan class di `app/models/`.
2. Import model di `app/models/__init__.py`.
3. Jalankan `alembic revision --autogenerate -m "pesan perubahan"`.
4. Jalankan `alembic upgrade head`.

## 🤖 Cara Mengoptimasi Prompt AI
1. Uji prompt di Google AI Studio terlebih dahulu.
2. Gunakan "Few-shot prompting" jika output tidak konsisten.
3. Pastikan output selalu divalidasi dengan Pydantic setelah diparsing dari JSON.

## 🔍 Cara Debugging
1. Gunakan `fastapi dev` untuk auto-reload.
2. Cek log container: `docker logs -f api`.
3. Gunakan `/docs` (Swagger UI) untuk testing manual input.

## 📦 Deployment Checklist (Coming Soon)
- [ ] Database backup strategy
- [ ] SSL Configuration with Caddy
- [ ] Vercel environment variables sync
