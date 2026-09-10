import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core import auth
from app.database.base import Base
from app.database.models import Organization


def test_production_denies_missing_whop_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    monkeypatch.setattr(auth, "SessionLocal", session_local)

    class Settings:
        app_env = "production"
        whop_required_product_id = None

    monkeypatch.setattr(auth, "get_settings", lambda: Settings())
    with pytest.raises(Exception) as raised:
        auth.require_organization_context(None, None)
    assert getattr(raised.value, "status_code", None) == 401


def test_organization_context_cannot_read_another_tenant(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session_local = sessionmaker(bind=engine)
    monkeypatch.setattr(auth, "SessionLocal", session_local)
    with session_local() as session:
        first = Organization(name="One", status="active")
        second = Organization(name="Two", status="active")
        session.add_all([first, second])
        session.commit()
        assert first.id != second.id
