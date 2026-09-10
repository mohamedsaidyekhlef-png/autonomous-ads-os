"""Verified, idempotent Whop membership webhook receiver."""

import hashlib
import hmac
import json
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.settings import get_settings
from app.database.models import Membership, Organization, User, WebhookEventRecord
from app.database.session import SessionLocal

router = APIRouter(prefix="/v1/webhooks", tags=["Whop"])


def _signature_valid(body: bytes, signature: str | None) -> bool:
    secret = get_settings().whop_webhook_secret
    if not secret or not signature:
        return False
    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature.removeprefix("sha256="))


def _value(payload: dict[str, Any], *names: str) -> str | None:
    data = payload.get("data") if isinstance(payload.get("data"), dict) else payload
    for name in names:
        value = data.get(name) or payload.get(name)
        if value is not None:
            return str(value)
    return None


def _membership_status(event_type: str) -> str:
    normalized = event_type.lower()
    if any(word in normalized for word in ("cancel", "expire", "deactivate")):
        return "cancelled" if "cancel" in normalized else "expired"
    return "active"


def process_whop_event(event_id: str, event_type: str, payload: dict[str, Any]) -> bool:
    """Returns False for an already-processed delivery."""
    company_id = _value(payload, "company_id", "companyId")
    user_id = _value(payload, "user_id", "userId")
    membership_id = _value(payload, "membership_id", "membershipId", "id")
    product_id = _value(payload, "product_id", "productId")
    if not company_id or not user_id or not membership_id:
        raise HTTPException(422, "Whop membership event is missing stable identifiers.")
    with SessionLocal() as database:
        already = database.scalars(
            select(WebhookEventRecord).where(WebhookEventRecord.event_id == event_id)
        ).first()
        if already:
            return False
        org = database.scalars(
            select(Organization).where(Organization.whop_company_id == company_id)
        ).one_or_none()
        if org is None:
            org = Organization(
                name=f"Whop organization {company_id}",
                whop_company_id=company_id,
                status="active",
                automation_enabled=False,
                risk_profile="conservative",
                daily_spend_cap_minor=0,
                monthly_spend_cap_minor=0,
                currency="USD",
            )
            database.add(org)
            database.flush()
        user = database.scalars(
            select(User).where(User.whop_user_id == user_id)
        ).one_or_none()
        if user is None:
            user = User(
                whop_user_id=user_id,
                email=_value(payload, "email"),
                display_name=_value(payload, "name"),
                status="active",
            )
            database.add(user)
            database.flush()
        membership = database.scalars(
            select(Membership).where(Membership.whop_membership_id == membership_id)
        ).one_or_none()
        if membership is None:
            membership = Membership(
                organization_id=org.id,
                user_id=user.id,
                whop_membership_id=membership_id,
                whop_product_id=product_id,
                status=_membership_status(event_type),
                role="owner",
                plan_code="whop",
            )
            database.add(membership)
        else:
            membership.status = _membership_status(event_type)
            membership.whop_product_id = product_id or membership.whop_product_id
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
    body = await request.body()
    signature = request.headers.get("x-whop-signature") or request.headers.get(
        "whop-signature"
    )
    if not _signature_valid(body, signature):
        raise HTTPException(401, "Whop webhook signature is invalid.")
    try:
        payload = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(400, "Whop webhook payload is invalid JSON.") from exc
    event_id = request.headers.get("x-whop-event-id") or str(payload.get("id", ""))
    event_type = str(
        payload.get("type") or payload.get("event") or "membership.updated"
    )
    if not event_id:
        raise HTTPException(422, "Whop webhook event id is required.")
    processed = process_whop_event(event_id, event_type, payload)
    return {"received": True, "processed": processed}
