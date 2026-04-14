# EduSolve AI Roadmap

## Phase 1: Foundation (Current)
- [x] Backend Boilerplate setup (FastAPI)
- [x] Database Schema Design (PostgreSQL + pgvector)
- [x] Guidelines & Documentation (Rules, Skills, README)
- [ ] Docker Environment Stabilization

## Phase 2: Core AI Engine
- [ ] Gemini 1.5 Flash Vision integration (Image-to-Text/Solution)
- [ ] LangChain Core workflow setup
- [ ] Retrieval Logic (pgvector query service)
- [ ] Document processing script (PDF to Chunks/Embeddings)

## Phase 3: API Endpoints
- [ ] `POST /api/v1/solve`: Main entry for image/text solutions
- [ ] `GET /api/v1/history`: User session history
- [ ] `POST /api/v1/feedback`: Data flywheel mechanism

## Phase 4: Frontend (Next.js)
- [ ] Initial UI Setup (Tailwind + KaTeX)
- [ ] Image upload & Camera integration
- [ ] Real-time solution rendering

## Phase 5: Deployment & Polish
- [ ] VPS Deployment (Caddy + Docker)
- [ ] Monitoring & Feedback dashboard
