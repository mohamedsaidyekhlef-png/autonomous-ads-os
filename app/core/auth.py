"""Organization-bound authentication and Whop entitlement checks."""

import uuid
from dataclasses import dataclass

from fastapi import Header, HTTPException
from sqlalchemy import select

from app.core.settings import get_settings
from app.database.models import Membership, Organization, User
from app.database.session import SessionLocal

ACTIVE_MEMBERSHIP_STATUSES = {"active", "trialing"}


@dataclass(frozen=True)
class OrganizationContext:
    organization_id: uuid.UUID
    user_id: uuid.UUID | None
    role: str


def require_organization_context(
    x_organization_id: str | None = Header(default=None),
    x_whop_user_id: str | None = Header(default=None),
) -> OrganizationContext:
    """Resolve org context and deny production access without Whop membership."""
    settings = get_settings()
    if not x_organization_id:
        if settings.app_env == "development":
            with SessionLocal() as database:
                organization = database.scalars(
                    select(Organization)
                    .where(Organization.status == "active")
                    .order_by(Organization.created_at)
                    .limit(1)
                ).first()
                if organization:
                    return OrganizationContext(organization.id, None, "owner")
        raise HTTPException(401, "Authenticated organization context is required.")
    try:
        organization_id = uuid.UUID(x_organization_id)
    except ValueError as exc:
        raise HTTPException(400, "X-Organization-ID is invalid.") from exc
    with SessionLocal() as database:
        organization = database.get(Organization, organization_id)
        if organization is None or organization.status != "active":
            raise HTTPException(404, "Organization was not found.")
        if settings.app_env == "development" and not x_whop_user_id:
            return OrganizationContext(organization_id, None, "owner")
        if not x_whop_user_id:
            raise HTTPException(401, "Verified Whop user context is required.")
        user = database.scalars(
            select(User).where(User.whop_user_id == x_whop_user_id)
        ).one_or_none()
        if user is None:
            raise HTTPException(403, "Whop access is not active.")
        membership = database.scalars(
            select(Membership).where(
                Membership.organization_id == organization_id,
                Membership.user_id == user.id,
                Membership.status.in_(ACTIVE_MEMBERSHIP_STATUSES),
            )
        ).first()
        if membership is None:
            raise HTTPException(403, "Whop access is not active.")
        if (
            settings.whop_required_product_id
            and membership.whop_product_id != settings.whop_required_product_id
        ):
            raise HTTPException(403, "Whop product entitlement is not active.")
        return OrganizationContext(organization_id, user.id, membership.role)
