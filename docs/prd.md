# Product Requirements Document (PRD)

**Project Name:** EduSolve AI
**Target Release:** 21 April
**Platform:** Web Application

## 1. Core Objective

An intelligent web-based study assistant capable of solving factual/exact-answer questions (Math, Physics, English) from uploaded images. The system must use Retrieval-Augmented Generation (RAG) to ensure high accuracy and output responses in a structured academic format.

## 2. Core Features (MVP)

- **Image-to-Solution:** Extract context from uploaded images/screenshots and solve the problem.
- **Contextual RAG:** Utilize vector search (`pgvector`) on uploaded lesson PDFs to provide factual grounding.
- **Math Rendering:** Render complex mathematical formulas using LaTeX/KaTeX in the UI.
- **Session History:** Save past user queries and AI responses for future retrieval.
- **Data Flywheel:** Include a 👍/👎 feedback mechanism on responses to collect accuracy metrics in the database.

## 3. Tech Stack Architecture

- **Frontend:** Next.js (React), Tailwind CSS, KaTeX.
- **Backend:** Python (FastAPI), LangChain.
- **AI Models:** Gemini 1.5 Flash (Vision & Logic), text-embedding-004.
- **Database:** Supabase (PostgreSQL with `pgvector`).
- **Deployment:** Docker container on VPS (Ubuntu) with Caddy Server (Reverse Proxy/SSL), Vercel for Frontend.

## 4. Logical Workflow

1. Client sends image/text payload to FastAPI endpoint.
2. FastAPI converts query to embeddings and retrieves top 3 relevant text chunks from Supabase.
3. FastAPI constructs a structured prompt combining System Instructions, Retrieved Context, and User Input.
4. Gemini API processes the prompt and returns a structured response (Concept, Steps, Final Answer).
5. FastAPI saves the transaction to the database and returns the markdown-formatted response to the client.
