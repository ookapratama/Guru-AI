from fastapi import APIRouter
from app.api.v1.endpoints import solve, history, health, ingest

api_router = APIRouter()
api_router.include_router(solve.router, prefix="/solve", tags=["Solve"])
api_router.include_router(history.router, prefix="/history", tags=["History"])
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(ingest.router, tags=["Admin"])
# api_router.include_router(feedback.router, prefix="/feedback", tags=["Feedback"])
