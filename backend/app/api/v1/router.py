from fastapi import APIRouter

from .endpoints import auth, briefs, checkins

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(checkins.router)
api_router.include_router(briefs.router)
