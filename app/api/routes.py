from fastapi import APIRouter
from app.api.endpoints.submission import submission_router
api_router = APIRouter()

api_router.include_router(submission_router, prefix="/submissions", tags=["submissions"])