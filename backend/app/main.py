from __future__ import annotations

import csv
import io
from datetime import date, datetime, timedelta
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response
from pydantic import BaseModel
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from sqlmodel import Session, select

from .database import get_session, init_db
from .models import (
    Account,
    Asset,
    Deal,
    Entry,
    FollowUp,
    MonthlySnapshot,
    PlayEnum,
    Routine,
    Template,
    WeeklySnapshot,
)
from .reporting import generate_monthly, generate_weekly, week_start_for
from .rules import extract_followups, infer_intention_bucket, infer_outcomes, infer_play, infer_tags

app = FastAPI(title="Local First Worklog")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EntryCreate(BaseModel):
    type: str = "note"
    title: str
    raw_note: str
    account_id: int | None = None
    deal_id: int | None = None
    duration_min: int = 15
    stakeholders: list[str] = []


class DealStageUpdate(BaseModel):
    stage: str


@app.on_event("startup")
def startup():
    init_db()


@app.post("/api/init")
def seed(session: Session = Depends(get_session)):
    if session.exec(select(Account)).first():
        return {"status": "already seeded"}

    accounts = [
        Account(name="Acme Retail", industry="Retail", segment="Enterprise"),
        Account(name="Northwind Health", industry="Healthcare", segment="Mid"),
    ]
    session.add_all(accounts)
    session.commit()
    session.refresh(accounts[0])
    session.refresh(accounts[1])

    deals = [
        Deal(account_id=accounts[0].id, name="Acme GCVE Migration", play_type="GCVE", stage="Discovery", next_step="Workshop", next_step_date=date.today()+timedelta(days=3), owners=["AE", "SE"], est_value=250000, est_fm=50000),
        Deal(account_id=accounts[1].id, name="Northwind AI Foundation", play_type="AI Readiness", stage="Proposal", next_step="Send SOW", next_step_date=date.today()+timedelta(days=5), owners=["AE"], est_value=350000, est_fm=70000),
    ]
    session.add_all(deals)

    routines = [
        Routine(routine_type="pipeline pod", frequency="weekly", default_day="Tue"),
        Routine(routine_type="co-sell touchpoint", frequency="weekly", default_day="Thu"),
        Routine(routine_type="learning block", frequency="weekly", default_day="Fri"),
        Routine(routine_type="enablement", frequency="twice-monthly", default_day="1st & 3rd Wed"),
        Routine(routine_type="win story", frequency="quarterly", default_day="last week"),
    ]
    session.add_all(routines)

    templates = [
        Template(template_type="weekly", content_md="Numbers first weekly template", is_default=True),
        Template(template_type="monthly", content_md="Monthly summary template", is_default=True),
    ]
    session.add_all(templates)
    session.commit()
    session.refresh(deals[0])
    session.refresh(deals[1])

    sample_notes = [
        "Ran pipeline pod for 7 deals, blocker flagged, follow up by Friday",
        "Delivered enablement talk track deck and objection handling",
        "Learning block: AI readiness checklist lab",
        "Co-sell touchpoint shared datasheet and one-pager",
    ]
    for note in sample_notes:
        e = Entry(
            type="meeting",
            title=note.split(":")[0][:50],
            raw_note=note,
            play=PlayEnum(infer_play(note)) if infer_play(note) in [e.value for e in PlayEnum] else PlayEnum.OTHER,
            tags=infer_tags(note),
            account_id=accounts[0].id,
            deal_id=deals[0].id,
            duration_min=30,
            outcomes=infer_outcomes(note),
            followups=extract_followups(note),
            intention_bucket=infer_intention_bucket(note, "meeting"),
        )
        session.add(e)
    session.commit()
    return {"status": "seeded"}


@app.get("/api/home")
def home(session: Session = Depends(get_session)):
    today = date.today()
    start = datetime.combine(today, datetime.min.time())
    end = datetime.combine(today, datetime.max.time())
    entries = session.exec(select(Entry).where(Entry.timestamp >= start, Entry.timestamp <= end)).all()
    due_end = week_start_for(today) + timedelta(days=6)
    followups = session.exec(select(FollowUp).where(FollowUp.status == "open", FollowUp.due_date <= due_end)).all()
    deals_due = session.exec(select(Deal).where(Deal.next_step_date <= due_end)).all()
    return {
        "today": {
            "time_logged": sum(e.duration_min for e in entries),
            "entries": len(entries),
            "accounts_touched": len({e.account_id for e in entries if e.account_id}),
            "deals_touched": len({e.deal_id for e in entries if e.deal_id}),
            "followups_due": len(followups),
        },
        "due_this_week": {
            "followups": [f.model_dump() for f in followups],
            "deals": [d.model_dump() for d in deals_due],
        },
    }


@app.get("/api/accounts")
def list_accounts(session: Session = Depends(get_session)):
    return session.exec(select(Account)).all()


@app.get("/api/deals")
def list_deals(account_id: int | None = None, session: Session = Depends(get_session)):
    stmt = select(Deal)
    if account_id:
        stmt = stmt.where(Deal.account_id == account_id)
    return session.exec(stmt).all()


@app.patch("/api/deals/{deal_id}/stage")
def update_deal_stage(deal_id: int, payload: DealStageUpdate, session: Session = Depends(get_session)):
    deal = session.get(Deal, deal_id)
    if not deal:
        raise HTTPException(404, "Deal not found")
    old = deal.stage
    deal.stage = payload.stage
    deal.updated_at = datetime.utcnow()
    session.add(deal)
    session.add(
        Entry(
            type="deal",
            title="Deal moved",
            raw_note=f"Deal moved: {old} → {payload.stage}",
            play=PlayEnum.OTHER,
            deal_id=deal.id,
            account_id=deal.account_id,
            duration_min=5,
            intention_bucket="D",
        )
    )
    session.commit()
    return {"status": "ok"}


@app.post("/api/entries")
def create_entry(payload: EntryCreate, session: Session = Depends(get_session)):
    play = infer_play(payload.raw_note)
    entry = Entry(
        type=payload.type,
        title=payload.title,
        raw_note=payload.raw_note,
        play=PlayEnum(play) if play in [e.value for e in PlayEnum] else PlayEnum.OTHER,
        tags=infer_tags(payload.raw_note),
        account_id=payload.account_id,
        deal_id=payload.deal_id,
        duration_min=payload.duration_min,
        stakeholders=payload.stakeholders,
        outcomes=infer_outcomes(payload.raw_note),
        followups=extract_followups(payload.raw_note),
        intention_bucket=infer_intention_bucket(payload.raw_note, payload.type),
    )
    session.add(entry)
    session.commit()
    session.refresh(entry)
    for fu in entry.followups:
        session.add(FollowUp(title=fu["title"], due_date=date.fromisoformat(fu["due_date"]), status="open", linked_entry_id=entry.id, linked_deal_id=entry.deal_id))
    session.commit()
    return entry


@app.get("/api/search")
def search(q: str = Query(""), session: Session = Depends(get_session)):
    ql = f"%{q.lower()}%"
    entries = session.exec(select(Entry).where(Entry.raw_note.ilike(ql))).all()
    deals = session.exec(select(Deal).where(Deal.name.ilike(ql))).all()
    return {"entries": entries, "deals": deals}


@app.post("/api/generate/weekly")
def generate_weekly_all(session: Session = Depends(get_session)):
    data = generate_weekly(session)
    snap = WeeklySnapshot(
        week_start=data["start"],
        teams_text=data["teams"],
        email_subject=data["subject"],
        email_body=data["email"],
        slide_bullets=data["slide"],
        metrics_json=data["metrics"],
    )
    session.add(snap)
    session.commit()
    return {
        "teams": data["teams"],
        "email_subject": data["subject"],
        "email_body": data["email"],
        "slide_bullets": data["slide"],
        "snapshot_id": snap.id,
    }


@app.post("/api/generate/monthly")
def generate_monthly_all(session: Session = Depends(get_session)):
    data = generate_monthly(session)
    snap = MonthlySnapshot(
        month_yyyy_mm=data["month"],
        teams_text=data["teams"],
        email_subject=data["subject"],
        email_body=data["email"],
        slide_bullets=data["slide"],
        metrics_json=data["metrics"],
    )
    session.add(snap)
    session.commit()
    return {
        "teams": data["teams"],
        "email_subject": data["subject"],
        "email_body": data["email"],
        "slide_bullets": data["slide"],
        "snapshot_id": snap.id,
    }


@app.post("/api/generate/slides")
def generate_slides(session: Session = Depends(get_session)):
    weekly = generate_weekly(session)
    return {"slide_bullets": weekly["slide"]}


@app.get("/api/reports/weekly")
def list_weekly(session: Session = Depends(get_session)):
    return session.exec(select(WeeklySnapshot).order_by(WeeklySnapshot.generated_at.desc())).all()


@app.get("/api/reports/monthly")
def list_monthly(session: Session = Depends(get_session)):
    return session.exec(select(MonthlySnapshot).order_by(MonthlySnapshot.generated_at.desc())).all()


def _to_pdf(title: str, content: str) -> bytes:
    packet = io.BytesIO()
    p = canvas.Canvas(packet, pagesize=letter)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(72, 760, title)
    p.setFont("Helvetica", 10)
    y = 735
    for line in content.split("\n"):
        p.drawString(72, y, line[:110])
        y -= 14
        if y < 72:
            p.showPage()
            y = 760
    p.save()
    return packet.getvalue()


@app.get("/api/export/{kind}/{fmt}")
def export(kind: str, fmt: str, session: Session = Depends(get_session)):
    if kind == "weekly":
        data = generate_weekly(session)
        title, content = data["subject"], f"{data['teams']}\n\n{data['email']}\n\n{data['slide']}"
    elif kind == "monthly":
        data = generate_monthly(session)
        title, content = data["subject"], f"{data['teams']}\n\n{data['email']}\n\n{data['slide']}"
    elif kind in {"entries", "deals", "assets"} and fmt == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        if kind == "entries":
            rows = session.exec(select(Entry)).all()
            writer.writerow(["id", "timestamp", "type", "title", "play", "duration_min", "intention_bucket"])
            for r in rows:
                writer.writerow([r.id, r.timestamp, r.type, r.title, r.play, r.duration_min, r.intention_bucket])
        elif kind == "deals":
            rows = session.exec(select(Deal)).all()
            writer.writerow(["id", "name", "stage", "next_step", "next_step_date", "est_value"])
            for r in rows:
                writer.writerow([r.id, r.name, r.stage, r.next_step, r.next_step_date, r.est_value])
        else:
            rows = session.exec(select(Asset)).all()
            writer.writerow(["id", "date", "asset_type", "title", "effort_min"])
            for r in rows:
                writer.writerow([r.id, r.date, r.asset_type, r.title, r.effort_min])
        return PlainTextResponse(output.getvalue(), media_type="text/csv")
    else:
        raise HTTPException(400, "Unsupported export")

    if fmt == "md":
        return PlainTextResponse(f"# {title}\n\n{content}")
    if fmt == "pdf":
        return Response(_to_pdf(title, content), media_type="application/pdf")
    raise HTTPException(400, "Unsupported format")
