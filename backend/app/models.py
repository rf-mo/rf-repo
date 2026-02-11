from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime, JSON, Text
from sqlmodel import Field, SQLModel


class PlayEnum(str, Enum):
    GCVE = "GCVE"
    GDC = "GDC"
    GKE = "GKE"
    VERTEX = "Vertex"
    FINOPS = "FinOps"
    AI_READINESS = "AI Readiness"
    OTHER = "Other"


class Entry(SQLModel, table=True):
    __tablename__ = "entries"

    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    type: str
    title: str
    raw_note: str
    play: PlayEnum = Field(default=PlayEnum.OTHER)
    tags: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    account_id: Optional[int] = Field(default=None, foreign_key="accounts.id")
    deal_id: Optional[int] = Field(default=None, foreign_key="deals.id")
    duration_min: int = 15
    stakeholders: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    outcomes: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    followups: list[dict] = Field(default_factory=list, sa_column=Column(JSON))
    intention_bucket: str = "D"
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Account(SQLModel, table=True):
    __tablename__ = "accounts"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    industry: str = ""
    segment: str = ""
    notes: str = ""


class Deal(SQLModel, table=True):
    __tablename__ = "deals"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_id: int = Field(foreign_key="accounts.id")
    name: str
    play_type: str
    stage: str
    est_value: Optional[float] = None
    est_fm: Optional[float] = None
    probability: Optional[float] = None
    next_step: str = ""
    next_step_date: Optional[date] = None
    owners: list[str] = Field(default_factory=list, sa_column=Column(JSON))
    notes: str = ""
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Asset(SQLModel, table=True):
    __tablename__ = "assets"

    id: Optional[int] = Field(default=None, primary_key=True)
    date: date = Field(default_factory=date.today)
    asset_type: str
    title: str
    linked_account_id: Optional[int] = Field(default=None, foreign_key="accounts.id")
    linked_deal_id: Optional[int] = Field(default=None, foreign_key="deals.id")
    effort_min: int = 30
    file_path: Optional[str] = None
    notes: str = ""


class FollowUp(SQLModel, table=True):
    __tablename__ = "followups"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    due_date: date
    status: str = "open"
    linked_entry_id: Optional[int] = Field(default=None, foreign_key="entries.id")
    linked_deal_id: Optional[int] = Field(default=None, foreign_key="deals.id")


class Routine(SQLModel, table=True):
    __tablename__ = "routines"

    id: Optional[int] = Field(default=None, primary_key=True)
    routine_type: str
    frequency: str
    default_day: str
    last_completed_date: Optional[date] = None
    is_active: bool = True


class WeeklySnapshot(SQLModel, table=True):
    __tablename__ = "snapshots_weekly"

    id: Optional[int] = Field(default=None, primary_key=True)
    week_start: date
    teams_text: str = Field(sa_column=Column(Text))
    email_subject: str
    email_body: str = Field(sa_column=Column(Text))
    slide_bullets: str = Field(sa_column=Column(Text))
    metrics_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    generated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=False)))


class MonthlySnapshot(SQLModel, table=True):
    __tablename__ = "snapshots_monthly"

    id: Optional[int] = Field(default=None, primary_key=True)
    month_yyyy_mm: str
    teams_text: str = Field(sa_column=Column(Text))
    email_subject: str
    email_body: str = Field(sa_column=Column(Text))
    slide_bullets: str = Field(sa_column=Column(Text))
    metrics_json: dict = Field(default_factory=dict, sa_column=Column(JSON))
    generated_at: datetime = Field(default_factory=datetime.utcnow, sa_column=Column(DateTime(timezone=False)))


class Template(SQLModel, table=True):
    __tablename__ = "templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    template_type: str
    content_md: str = Field(sa_column=Column(Text))
    is_default: bool = True
