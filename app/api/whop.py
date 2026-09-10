"""Standard Webhooks verified Whop membership synchronization."""

from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from standardwebhooks.webhooks import Webhook, WebhookVerificationError

from app.core.settings import get_settings
from app.database.models import (
    Membership,
    Organization,
    User,
    WebhookEventRecord,
)
from app.database.session import SessionLocal

router = APIRouter(prefix="/v1/webhooks", tags=["Whop"])

EVENT_STATUS = {
    "membership.activated": "active",
    "membership.deactivated": "cancelled",
    "membership.went_valid": "active",
    "membership.went_invalid": "expired",
}


def _value(payload: dict[str, Any], *names: str) -> str | None:
    data = payload.get("data")
    source = data if isinstance(data, dict) else payload

    for name in names:
        value = source.get(name)
        if value is None:
            value = payload.get(name)
        if value is not None:
            return str(value)

    return None


def _status_for_event(event_type: str) -> str | None:
    return EVENT_STATUS.get(event_type)


def process_whop_event(
    event_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> bool:
    """Synchronize one verified event; return False for duplicates/unknowns."""

    status = _status_for_event(event_type)
    if status is None:
        return False

    account_id = _value(
        payload,
        "account_id",
        "company_id",
        "companyId",
    )
    user_id = _value(payload, "user_id", "userId")
    membership_id = _value(
        payload,
        "membership_id",
        "membershipId",
        "id",
    )
    product_id = _value(payload, "product_id", "productId")

    if not account_id or not user_id or not membership_id:
        raise HTTPException(
            422,
            "Whop membership event is missing stable identifiers.",
        )

    with SessionLocal() as database:
        duplicate = database.scalars(
            select(WebhookEventRecord).where(WebhookEventRecord.event_id == event_id)
        ).first()

        if duplicate is not None:
            return False

        organization = database.scalars(
            select(Organization).where(Organization.whop_company_id == account_id)
        ).one_or_none()

        if organization is None:
            organization = Organization(
                name=f"Whop organization {account_id}",
                whop_company_id=account_id,
                status="active",
                automation_enabled=False,
                risk_profile="conservative",
                daily_spend_cap_minor=0,
                monthly_spend_cap_minor=0,
                currency="USD",
            )
            database.add(organization)
            database.flush()

        user = database.scalars(
            select(User).where(User.whop_user_id == user_id)
        ).one_or_none()

        if user is None:
            user = User(
                whop_user_id=user_id,
                email=_value(payload, "email"),
                display_name=_value(payload, "name", "username"),
                status="active",
            )
            database.add(user)
            database.flush()

        membership = database.scalars(
            select(Membership).where(Membership.whop_membership_id == membership_id)
        ).one_or_none()

        if membership is None:
            membership = Membership(
                organization_id=organization.id,
                user_id=user.id,
                whop_membership_id=membership_id,
                whop_product_id=product_id,
                status=status,
                role="owner",
                plan_code="whop",
            )
            database.add(membership)
        else:
            membership.status = status
            if product_id:
                membership.whop_product_id = product_id

        database.add(
            WebhookEventRecord(
                provider="whop",
                event_id=event_id,
                event_type=event_type,
                payload=payload,
                processed_at=datetime.now(UTC),
            )
        )

        try:
            database.commit()
        except IntegrityError:
            database.rollback()
            return False

    return True


@router.post("/whop")
async def whop_webhook(request: Request) -> dict[str, Any]:
    secret = get_settings().whop_webhook_secret

    if not secret:
        raise HTTPException(503, "Whop webhook verification is not configured.")

    body = await request.body()

    try:
        payload = Webhook(secret).verify(body, dict(request.headers))
    except (WebhookVerificationError, ValueError, TypeError) as exc:
        raise HTTPException(
            401,
            "Whop webhook signature is invalid.",
        ) from exc

    if not isinstance(payload, dict):
        raise HTTPException(400, "Whop webhook payload is invalid.")

    event_id = request.headers.get("webhook-id")
    event_type = str(payload.get("type") or payload.get("event") or "")

    if not event_id:
        raise HTTPException(422, "Verified webhook ID is required.")

    if event_type not in EVENT_STATUS:
        return {
            "received": True,
            "processed": False,
            "reason": "unsupported_event",
        }

    processed = process_whop_event(event_id, event_type, payload)

    return {
        "received": True,
        "processed": processed,
    }
