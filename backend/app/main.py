import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.v1.router import api_router
from .core.config import settings
from .db import init_db

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.on_event("startup")
def on_startup() -> None:
    try:
        init_db()
    except Exception:  # pragma: no cover - startup warning path
        logging.warning("PostgreSQL unavailable at startup; upload endpoint will return 503.")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
