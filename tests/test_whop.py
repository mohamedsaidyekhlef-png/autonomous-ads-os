import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import whop
from app.database.base import Base
from app.database.models import Membership


def test_whop_event_is_idempotent(monkeypatch: pytest.MonkeyPatch) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(whop, "SessionLocal", session_local)
    event = {
        "company_id": "company_1",
        "user_id": "user_1",
        "membership_id": "membership_1",
        "product_id": "product_1",
    }
    assert whop.process_whop_event("event_1", "membership.activated", event)
    assert not whop.process_whop_event("event_1", "membership.activated", event)
    assert whop.process_whop_event("event_2", "membership.deactivated", event)
    with session_local() as session:
        membership = session.query(Membership).one()
        assert membership.status == "cancelled"
