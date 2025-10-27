import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import ALLOW_ORIGINS
from app.routers import api_router


app = FastAPI(title="Tip-Trip Backend (scaffold)")


app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health():
    """Basic healthcheck endpoint."""
    return {"status": "ok"}
