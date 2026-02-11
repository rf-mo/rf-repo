from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

from sqlmodel import Session, select

from .models import Asset, Deal, Entry, FollowUp, Routine
from .rules import count_unique


def week_start_for(day: date) -> date:
    return day - timedelta(days=day.weekday())


def month_key_for(day: date) -> str:
    return day.strftime("%Y-%m")


def _collect_metrics(entries: list[Entry], session: Session, start: date, end: date) -> dict:
    by_type = Counter(e.type for e in entries)
    hours_by_play = defaultdict(float)
    for e in entries:
        hours_by_play[e.play.value if hasattr(e.play, "value") else str(e.play)] += e.duration_min / 60.0

    followups = session.exec(select(FollowUp).where(FollowUp.due_date >= start, FollowUp.due_date <= end)).all()
    assets = session.exec(select(Asset).where(Asset.date >= start, Asset.date <= end)).all()
    deals = session.exec(select(Deal).where(Deal.updated_at >= datetime.combine(start, datetime.min.time()), Deal.updated_at <= datetime.combine(end, datetime.max.time()))).all()
    routines = session.exec(select(Routine).where(Routine.is_active == True)).all()  # noqa: E712
    completed = sum(1 for r in routines if r.last_completed_date and start <= r.last_completed_date <= end)

    influenced = sum(d.est_value or 0 for d in deals)
    influenced_fm = sum(d.est_fm or 0 for d in deals)

    return {
        "entry_counts_by_type": dict(by_type),
        "hours_by_play": {k: round(v, 2) for k, v in hours_by_play.items()},
        "cadence_completion_rate": round(completed / max(len(routines), 1), 2),
        "accounts_touched": count_unique([e.account_id for e in entries]),
        "deals_touched": count_unique([e.deal_id for e in entries]),
        "assets_created": len(assets),
        "followups_closed": sum(1 for f in followups if f.status == "done"),
        "followups_created": len(followups),
        "influenced_value": influenced,
        "influenced_fm": influenced_fm,
    }


def _deals_lines(session: Session, start: date, end: date) -> list[str]:
    deals = session.exec(select(Deal).where(Deal.next_step_date >= start, Deal.next_step_date <= end)).all()
    return [f"- {d.name}: stage {d.stage}; next: {d.next_step} ({d.next_step_date})" for d in deals[:5]]


def generate_weekly(session: Session, today: date | None = None) -> dict:
    today = today or date.today()
    start = week_start_for(today)
    end = start + timedelta(days=6)
    entries = session.exec(
        select(Entry).where(Entry.timestamp >= datetime.combine(start, datetime.min.time()), Entry.timestamp <= datetime.combine(end, datetime.max.time()))
    ).all()
    metrics = _collect_metrics(entries, session, start, end)

    bullets = [
        f"{len(entries)} entries logged; {sum(e.duration_min for e in entries)} mins tracked across {metrics['accounts_touched']} accounts.",
        f"{metrics['deals_touched']} deals touched; cadence completion at {int(metrics['cadence_completion_rate']*100)}%.",
        f"{metrics['assets_created']} assets produced; {metrics['followups_created']} follow-ups created ({metrics['followups_closed']} closed).",
    ]
    if metrics["influenced_value"]:
        bullets.append(f"${metrics['influenced_value']:.0f} influenced pipeline tracked.")

    teams_text = "\n".join(f"- {b}" for b in bullets)
    subject = f"Weekly Update – Week of {start.strftime('%b %d')}"
    body = "\n".join(
        [
            "1) Highlights",
            *[f"- {b}" for b in bullets[:3]],
            "\n2) Deals & pipeline movement",
            *(_deals_lines(session, start, end) or ["- No deal updates logged."]),
            "\n3) Enablement & assets produced",
            f"- Assets created: {metrics['assets_created']}",
            "\n4) Co-sell touchpoints",
            f"- Entries tagged co-sell/talk track: {sum('talk track' in (e.raw_note or '').lower() for e in entries)}",
            "\n5) Risks/blockers",
            f"- Blockers flagged: {sum('blocker' in (e.raw_note or '').lower() for e in entries)}",
            "\n6) Next week focus",
            "- Progress top active deals and close open follow-ups.",
        ]
    )
    slide = "\n".join(
        [
            f"• {len(entries)} worklog updates / {sum(e.duration_min for e in entries)//60}h logged",
            f"• {metrics['deals_touched']} deals active, {metrics['followups_closed']}/{metrics['followups_created']} follow-ups closed",
            f"• Cadence completion {int(metrics['cadence_completion_rate']*100)}%",
            "• Focus: move next steps and reduce blockers",
        ]
    )
    return {"start": start, "teams": teams_text, "subject": subject, "email": body, "slide": slide, "metrics": metrics}


def generate_monthly(session: Session, today: date | None = None) -> dict:
    today = today or date.today()
    start = today.replace(day=1)
    end = (start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    entries = session.exec(
        select(Entry).where(Entry.timestamp >= datetime.combine(start, datetime.min.time()), Entry.timestamp <= datetime.combine(end, datetime.max.time()))
    ).all()
    metrics = _collect_metrics(entries, session, start, end)

    highlights = [
        f"{len(entries)} total entries, {sum(e.duration_min for e in entries)//60}h logged",
        f"{metrics['accounts_touched']} accounts and {metrics['deals_touched']} deals touched",
        f"{metrics['assets_created']} assets created and reused",
        f"Cadence completion: {int(metrics['cadence_completion_rate']*100)}%",
        f"Follow-ups: {metrics['followups_closed']} closed / {metrics['followups_created']} created",
    ]
    teams = "\n".join(f"- {h}" for h in highlights)
    subject = f"Monthly Summary – {start.strftime('%B %Y')}"
    proof = []
    raw = " ".join(e.raw_note.lower() for e in entries)
    for key in ["faster", "safer", "performance", "cost"]:
        if key in raw:
            proof.append(f"- Proof ({key}): observed in logged updates.")

    body = "\n".join(
        [
            "Top 5 highlights",
            *[f"- {h}" for h in highlights],
            "\nMetrics",
            f"- Counts by type: {metrics['entry_counts_by_type']}",
            f"- Hours by play: {metrics['hours_by_play']}",
            "\nProof statements",
            *(proof or ["- No explicit proof statements logged this month."]),
            "\nWin story status",
            f"- {'drafted' if 'win story' in raw else 'not drafted'}",
            "\nNext month priorities",
            "- Advance pipeline pods, complete enablement plan, and publish one win story.",
        ]
    )
    slide = "\n".join(f"• {h}" for h in highlights[:5])
    return {"month": month_key_for(today), "teams": teams, "subject": subject, "email": body, "slide": slide, "metrics": metrics}
