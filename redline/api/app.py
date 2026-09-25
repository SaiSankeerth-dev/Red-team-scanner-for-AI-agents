"""FastAPI surface for Redline.

Run campaigns over HTTP and browse results with full transcripts.

Run with (from ~/workspace/redline, venv active):
    uvicorn redline.api.app:app --reload
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
import os
import time

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from redline import cli as cli_module
from redline.adapters.local import LocalAgentAdapter
from redline.demo import DEMO_TARGETS
from redline.runner import CampaignRunner
from redline.store import db as db_module
from redline.store.models import AttemptRecord, Campaign


class CampaignCreate(BaseModel):
    target: str = "vulnerable"  # local demo name (adapter="local")
    pack: str = "basics"
    name: str | None = None
    adapter: str = "local"  # local | openai | http
    adapter_config: dict = {}  # e.g. {"model": ..., "api_key": ...} or {"url": ...}


class AttemptOut(BaseModel):
    id: int
    probe_name: str
    messages: list
    response: str | None
    verdict: str
    notes: str | None


class CampaignSummary(BaseModel):
    id: int
    name: str
    target: str
    pack: str
    created_at: datetime
    verdict_counts: dict[str, int]


class CampaignDetail(CampaignSummary):
    attempts: list[AttemptOut]


app = FastAPI(title="Redline", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        os.environ.get("DASHBOARD_ORIGIN", ""),
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- lightweight guard: optional bearer token + per-IP rate limit ---
# Set REDLINE_API_TOKEN to require `Authorization: Bearer <token>` on every
# route except /health. No token set -> open (local dev default).
_RATE_WINDOW_S = 60
_RATE_MAX = 240
_rate_hits: dict[str, list[float]] = {}


@app.middleware("http")
async def _guard(request: Request, call_next):
    if request.url.path != "/health":
        token = os.environ.get("REDLINE_API_TOKEN")
        if token and request.headers.get("authorization") != f"Bearer {token}":
            return JSONResponse({"detail": "unauthorized"}, status_code=401)
        now = time.monotonic()
        ip = request.client.host if request.client else "?"
        hits = _rate_hits.setdefault(ip, [])
        while hits and hits[0] <= now - _RATE_WINDOW_S:
            hits.pop(0)
        if len(hits) >= _RATE_MAX:
            return JSONResponse(
                {"detail": "rate limit exceeded, slow down"}, status_code=429
            )
        hits.append(now)
    return await call_next(request)


def get_session():
    engine = db_module.init_db()
    session = sessionmaker(bind=engine)()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _counts(session: Session, campaign_id: int) -> dict[str, int]:
    rows = session.query(AttemptRecord.verdict).filter_by(campaign_id=campaign_id).all()
    return dict(Counter(v for (v,) in rows))


def _attempts_out(session: Session, campaign_id: int) -> list[AttemptOut]:
    rows = (
        session.query(AttemptRecord)
        .filter_by(campaign_id=campaign_id)
        .order_by(AttemptRecord.id)
        .all()
    )
    return [
        AttemptOut(
            id=a.id,
            probe_name=a.probe_name,
            messages=a.messages,
            response=a.response,
            verdict=a.verdict,
            notes=a.notes,
        )
        for a in rows
    ]


@app.post("/campaigns", response_model=CampaignDetail, status_code=201)
def create_campaign(body: CampaignCreate, session: Session = Depends(get_session)):
    from redline.adapters.factory import build_adapter

    try:
        target, target_name = build_adapter(
            body.adapter, {"target": body.target, **body.adapter_config}
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    probe_classes = cli_module.PACKS.get(body.pack)
    if probe_classes is None:
        raise HTTPException(status_code=400, detail=f"unknown pack: {body.pack}")
    runner = CampaignRunner(session)
    result = runner.run_campaign(
        name=body.name or f"{target_name}/{body.pack}",
        target=target,
        target_name=target_name,
        probe_classes=probe_classes,
        pack_name=body.pack,
    )
    c = result.campaign
    return CampaignDetail(
        id=c.id,
        name=c.name,
        target=c.target,
        pack=c.pack,
        created_at=c.created_at,
        verdict_counts=_counts(session, c.id),
        attempts=_attempts_out(session, c.id),
    )


@app.get("/campaigns", response_model=list[CampaignSummary])
def list_campaigns(session: Session = Depends(get_session)):
    campaigns = session.query(Campaign).order_by(Campaign.id.desc()).all()
    return [
        CampaignSummary(
            id=c.id,
            name=c.name,
            target=c.target,
            pack=c.pack,
            created_at=c.created_at,
            verdict_counts=_counts(session, c.id),
        )
        for c in campaigns
    ]


@app.get("/campaigns/{campaign_id}", response_model=CampaignDetail)
def get_campaign(campaign_id: int, session: Session = Depends(get_session)):
    c = session.query(Campaign).filter_by(id=campaign_id).first()
    if c is None:
        raise HTTPException(status_code=404, detail="campaign not found")
    return CampaignDetail(
        id=c.id,
        name=c.name,
        target=c.target,
        pack=c.pack,
        created_at=c.created_at,
        verdict_counts=_counts(session, c.id),
        attempts=_attempts_out(session, c.id),
    )


@app.get("/campaigns/{campaign_id}/report")
def get_report(campaign_id: int, format: str = "html",
               session: Session = Depends(get_session)):
    """Scored report for a campaign: HTML page by default, PDF download with ?format=pdf."""
    from redline.reports.generator import build_report_data, render_html

    try:
        data = build_report_data(session, campaign_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="campaign not found")
    if format == "pdf":
        from redline.reports.pdf import render_pdf_bytes

        return Response(
            render_pdf_bytes(data),
            media_type="application/pdf",
            headers={"Content-Disposition":
                     f'attachment; filename="redline-campaign-{campaign_id}.pdf"'},
        )
    return HTMLResponse(render_html(data))


@app.get("/campaigns/{campaign_id}/summary")
def get_summary(campaign_id: int, session: Session = Depends(get_session)):
    """Machine-readable scored summary for a campaign (powers the dashboard)."""
    from redline.reports.generator import build_report_data

    try:
        return build_report_data(session, campaign_id)
    except LookupError:
        raise HTTPException(status_code=404, detail="campaign not found")
