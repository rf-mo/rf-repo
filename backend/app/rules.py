from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Iterable

PLAY_KEYWORDS = {
    "GCVE": ["gcve", "vmware", "migration"],
    "GDC": ["gdc", "data cloud", "data"],
    "GKE": ["gke", "kubernetes", "container"],
    "Vertex": ["vertex", "ml", "model"],
    "FinOps": ["finops", "cost", "optimization"],
    "AI Readiness": ["ai readiness", "ai", "inference", "gpu", "foundation"],
}

TAG_KEYWORDS = {
    "ATC": ["atc"],
    "funding": ["funding", "accelerator"],
    "workshop": ["workshop"],
    "SOW": ["sow", "statement of work"],
    "pod": ["pod", "pipeline"],
    "enablement": ["enablement", "training"],
    "talk track": ["talk track", "objection"],
    "objection": ["objection"],
    "win story": ["win story"],
    "checklist": ["checklist"],
    "demo": ["demo", "poc"],
    "sizing": ["sizing", "estimate"],
    "architecture": ["architecture", "design"],
}

OUTCOME_MAP = {
    "workshop": "workshop proposed",
    "scheduled": "workshop scheduled",
    "sow": "SOW started",
    "pod": "pipeline pod",
    "enablement": "enablement delivered",
    "talk track": "co-sell touchpoint",
    "deck": "asset created",
    "one-pager": "asset created",
    "datasheet": "asset created",
    "learn": "learning block",
    "stakeholder": "stakeholder update",
    "blocker": "blocker flagged",
    "follow up": "follow-up created",
}

INTENTION_KEYWORDS = {
    "A": ["co-sell", "accelerator", "pov", "why", "workshop", "sow", "win story", "datasheet"],
    "B": ["ai readiness", "infra", "foundation", "checklist", "talk track", "specialization"],
    "C": ["support", "learning", "template", "community", "risk", "balance", "focus"],
    "D": ["pipeline pod", "enablement session", "walk the halls", "cadence", "co-sell touchpoint"],
}

FOLLOWUP_PATTERNS = [
    r"follow\s?up",
    r"waiting on",
    r"send",
    r"need from",
    r"by\s+(friday|monday|tuesday|wednesday|thursday|\d{4}-\d{2}-\d{2})",
]


def _text(raw: str) -> str:
    return raw.lower().strip()


def infer_play(raw: str) -> str:
    t = _text(raw)
    for play, keys in PLAY_KEYWORDS.items():
        if any(k in t for k in keys):
            return play
    return "Other"


def infer_tags(raw: str) -> list[str]:
    t = _text(raw)
    tags = [tag for tag, keys in TAG_KEYWORDS.items() if any(k in t for k in keys)]
    return sorted(set(tags))


def infer_outcomes(raw: str) -> list[str]:
    t = _text(raw)
    hits = [outcome for key, outcome in OUTCOME_MAP.items() if key in t]
    if "meeting" in t:
        hits.append("meeting completed")
    return sorted(set(hits))[:5]


def infer_intention_bucket(raw: str, entry_type: str) -> str:
    t = f"{entry_type} {_text(raw)}"
    for bucket, keys in INTENTION_KEYWORDS.items():
        if any(k in t for k in keys):
            return bucket
    if "cadence" in t or "weekly" in t:
        return "D"
    return "A"


def extract_followups(raw: str, base_date: date | None = None) -> list[dict]:
    t = _text(raw)
    if not any(re.search(pattern, t) for pattern in FOLLOWUP_PATTERNS):
        return []

    due = base_date or date.today()
    if "friday" in t:
        days_ahead = (4 - due.weekday()) % 7
        due = due + timedelta(days=days_ahead or 7)
    m = re.search(r"(\d{4}-\d{2}-\d{2})", t)
    if m:
        due = datetime.strptime(m.group(1), "%Y-%m-%d").date()

    return [{"title": raw[:80], "due_date": due.isoformat(), "status": "open"}]


def count_unique(values: Iterable[int | None]) -> int:
    return len({v for v in values if v is not None})
