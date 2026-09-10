import base64
import json
from datetime import UTC, datetime

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from standardwebhooks.webhooks import Webhook, WebhookVerificationError

from app.api import whop
from app.core import auth
from app.database.base import Base
from app.database.models import Membership


def test_forged_legacy_headers_do_not_authenticate_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Settings:
        app_env = "production"
        development_auth_bypass = False
        whop_app_id = "app_test"
        whop_api_key = "key_test"
        whop_product_id = "prod_test"
        whop_required_product_id = "prod_test"

    monkeypatch.setattr(auth, "get_settings", lambda: Settings())

    with pytest.raises(HTTPException) as raised:
        auth.require_organization_context(
            "forged-organization",
            "user_forged",
            None,
        )

    assert raised.value.status_code == 401


def test_unknown_event_never_activates_membership(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    sessions = sessionmaker(bind=engine, expire_on_commit=False)
    monkeypatch.setattr(whop, "SessionLocal", sessions)

    payload = {
        "account_id": "biz_test",
        "user_id": "user_test",
        "membership_id": "mem_test",
        "product_id": "prod_test",
    }

    assert not whop.process_whop_event(
        "event_unknown",
        "membership.metadata_updated",
        payload,
    )

    with sessions() as database:
        assert database.query(Membership).count() == 0


def test_standard_webhook_signature_is_required(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class Settings:
        whop_webhook_secret = base64.b64encode(
            b"0123456789abcdef0123456789abcdef"
        ).decode()

    monkeypatch.setattr(whop, "get_settings", lambda: Settings())

    with pytest.raises(WebhookVerificationError):
        Webhook(Settings.whop_webhook_secret).verify(
            b'{"type":"membership.activated"}',
            {},
        )


def test_standard_webhook_valid_signature() -> None:
    secret = base64.b64encode(b"0123456789abcdef0123456789abcdef").decode()
    verifier = Webhook(secret)
    body = json.dumps({"type": "membership.activated"})
    timestamp = datetime.now(UTC)
    signature = verifier.sign(
        msg_id="event_valid",
        timestamp=timestamp,
        data=body,
    )

    payload = verifier.verify(
        body,
        {
            "webhook-id": "event_valid",
            "webhook-timestamp": str(int(timestamp.timestamp())),
            "webhook-signature": signature,
        },
    )

    assert payload["type"] == "membership.activated"
