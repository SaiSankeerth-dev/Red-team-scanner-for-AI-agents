"""Redline API (dashboard backend)."""
from __future__ import annotations

from fastapi import FastAPI

app = FastAPI(title="Redline API")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/campaigns")
def create_campaign() -> dict:
    return {"detail": "Phase 3: not implemented yet"}


@app.get("/campaigns")
def list_campaigns() -> list:
    return []
