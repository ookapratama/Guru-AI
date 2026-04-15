# EduSolve AI

Intelligent web-based study assistant for Math, Physics, and English. Capable of solving problems from images using RAG and Gemini 1.5 Flash.

## 🚀 Tech Stack

- **Backend:** FastAPI (Python), LangChain, Gemini 1.5 Flash
- **Database:** Supabase (PostgreSQL + `pgvector`)
- **Frontend:** Next.js (React), Tailwind CSS, KaTeX
- **DevOps:** Docker, Caddy Server, Vercel

## 📁 Project Structure

```text
.
├── backend/            # FastAPI Project
│   ├── app/            # Source code
│   ├── alembic/        # Migrations
│   ├── docs/           # Backend-specific documentation
│   └── ...
├── docs/               # Global documentation (PRD, Rules, etc.)
└── ...
```

## 🛠 Getting Started

### Prerequisites
- Python 3.11+
- Docker & Docker Compose
- Google AI API Key

### Installation

1. Clone the repository
2. Set up environment: `cp backend/.env.example backend/.env`
3. Run with Docker: `docker-compose up --build`

---

## 🧪 Testing Backend (EduSolve AI)

Bagian Backend (EduSolve AI Core) sudah mengimplementasikan endpoint utama `POST /api/v1/solve` yang memadukan **Pydantic Schemas**, **Supabase Vector Retrieval (RAG)**, dan **Gemini 1.5 Flash (Multimodal)**.

Untuk mengetesnya secara manual tanpa Docker, ikuti langkah berikut (butuh 2 terminal):

### 1. Setup Environment
Isi file `backend/.env` dengan API Key dari [Google AI Studio](https://aistudio.google.com/apikey):
```env
GOOGLE_API_KEY="AIzaSy.......your-real-key"
```

### 2. Jalankan Server (Terminal 1)
Buka terminal pertama untuk menyalakan FastAPI server:
```bash
cd backend
source venv/bin/activate
# Install deps jika belum: pip install -r requirements.txt
uvicorn app.main:app --port 8000 --reload
```
*(Biarkan terminal ini tetap berjalan)*

### 3. Jalankan Automate Test Script (Terminal 2)
Buka terminal **kedua** (pastikan server masih menyala di terminal pertama):
```bash
cd backend
source venv/bin/activate
python test_endpoints.py
```

Script test akan mengecek secara otomatis:
- ✅ Health check (`GET /`)
- ✅ Swagger Docs (`GET /docs`)
- ✅ Validasi Pydantic (menolak request tanpa field "image_base64")
- ✅ Request `/solve` pengujian penuh ke model AI (hanya berhasil *Success 200* jika `GOOGLE_API_KEY` valid, jika tidak akan return *502 Bad Gateway* secara _graceful_).

Anda juga dapat membuka Swagger UI di **http://localhost:8000/docs** untuk simulasi request `POST /solve` secara interaktif.

## 📖 Documentation

- [Product Requirements (PRD)](docs/prd.md)
- [Engineering Rules & Guidelines](docs/rules.md)
- [Development Skills & Workflows](docs/skills.md)

## ⚖️ License
MIT
