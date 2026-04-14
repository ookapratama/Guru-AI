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

## 📖 Documentation

- [Product Requirements (PRD)](docs/prd.md)
- [Engineering Rules & Guidelines](docs/rules.md)
- [Development Skills & Workflows](docs/skills.md)

## ⚖️ License
MIT
