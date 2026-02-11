from datetime import date, datetime

from sqlmodel import Session, SQLModel, create_engine

from app.models import Account, Deal, Entry, FollowUp, PlayEnum, Routine
from app.reporting import generate_monthly, generate_weekly


def build_session():
    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_weekly_and_monthly_generation_contains_expected_sections():
    with build_session() as session:
        account = Account(name="Test", industry="Tech", segment="Ent")
        session.add(account)
        session.commit()
        session.refresh(account)
        deal = Deal(account_id=account.id, name="Deal 1", play_type="GCVE", stage="Discovery", next_step="Call", next_step_date=date.today())
        session.add(deal)
        session.add(Routine(routine_type="pipeline pod", frequency="weekly", default_day="Tue", last_completed_date=date.today(), is_active=True))
        session.add(Entry(type="meeting", title="touchpoint", raw_note="pipeline pod talk track", play=PlayEnum.GCVE, account_id=account.id, deal_id=1, duration_min=30, intention_bucket="D", timestamp=datetime.utcnow()))
        session.add(FollowUp(title="Send notes", due_date=date.today(), status="done", linked_entry_id=1, linked_deal_id=1))
        session.commit()

        weekly = generate_weekly(session)
        monthly = generate_monthly(session)

        assert "Weekly Update" in weekly["subject"]
        assert "Highlights" in weekly["email"]
        assert "Monthly Summary" in monthly["subject"]
        assert "Top 5 highlights" in monthly["email"]
