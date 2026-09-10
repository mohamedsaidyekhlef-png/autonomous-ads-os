"""Verified Whop identity and organization-scoped authorization."""

import uuid
from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Header, HTTPException
from sqlalchemy import select
from whop_sdk import Whop
from whop_sdk.lib.verify_user_token import verify_user_token

from app.core.settings import get_settings
from app.database.models import Membership, Organization, User
from app.database.session import SessionLocal

ACTIVE_MEMBERSHIP_STATUSES = {"active", "trialing"}


@dataclass(frozen=True)
class OrganizationContext:
    organization_id: uuid.UUID
    user_id: uuid.UUID | None
    role: str


def _development_context() -> OrganizationContext:
    with SessionLocal() as database:
        organization = database.scalars(
            select(Organization)
            .where(Organization.status == "active")
            .order_by(Organization.created_at)
            .limit(1)
        ).first()

        if organization is None:
            raise HTTPException(409, "No active development organization exists.")

        return OrganizationContext(organization.id, None, "owner")


def _verified_whop_user_id(token: str | None, app_id: str | None) -> str:
    if not token:
        raise HTTPException(401, "Whop user token is required.")

    if not app_id:
        raise HTTPException(503, "Whop application identity is not configured.")

    try:
        payload: Any = verify_user_token(token, app_id=app_id)
        user_id = getattr(payload, "user_id", None)
    except Exception as exc:
        raise HTTPException(401, "Whop user token is invalid or expired.") from exc

    if not isinstance(user_id, str) or not user_id.startswith("user_"):
        raise HTTPException(401, "Whop user token contains no valid user identity.")

    return user_id


def _check_whop_access(
    user_id: str,
    api_key: str | None,
    resource_id: str | None,
) -> None:
    if not api_key or not resource_id:
        raise HTTPException(503, "Whop product access is not configured.")

    try:
        access = Whop(token=api_key).users.check_access(
            id=user_id,
            resource_id=resource_id,
        )
    except Exception as exc:
        raise HTTPException(503, "Whop access verification is unavailable.") from exc

    if not bool(getattr(access, "has_access", False)):
        raise HTTPException(403, "An active Whop subscription is required.")

    level = str(getattr(access, "access_level", "no_access"))
    if level not in {"customer", "admin"}:
        raise HTTPException(403, "An active Whop subscription is required.")


def require_organization_context(
    x_organization_id: Annotated[
        str | None,
        Header(alias="x-organization-id"),
    ] = None,
    x_whop_user_id: Annotated[
        str | None,
        Header(alias="x-whop-user-id"),
    ] = None,
    x_whop_user_token: Annotated[
        str | None,
        Header(alias="x-whop-user-token"),
    ] = None,
) -> OrganizationContext:
    """Authenticate with Whop and derive the organization from membership."""

    # These legacy headers are intentionally ignored in production. Keeping the
    # parameters temporarily avoids breaking older development clients.
    del x_organization_id, x_whop_user_id

    settings = get_settings()
    development_bypass = bool(getattr(settings, "development_auth_bypass", True))

    if (
        settings.app_env == "development"
        and development_bypass
        and not x_whop_user_token
    ):
        return _development_context()

    user_id = _verified_whop_user_id(
        x_whop_user_token,
        getattr(settings, "whop_app_id", None),
    )

    required_product = getattr(settings, "whop_required_product_id", None) or getattr(
        settings, "whop_product_id", None
    )

    _check_whop_access(
        user_id,
        getattr(settings, "whop_api_key", None),
        required_product,
    )

    with SessionLocal() as database:
        user = database.scalars(
            select(User).where(
                User.whop_user_id == user_id,
                User.status == "active",
            )
        ).one_or_none()

        if user is None:
            raise HTTPException(403, "Whop membership has not been synchronized.")

        memberships = database.scalars(
            select(Membership).where(
                Membership.user_id == user.id,
                Membership.status.in_(ACTIVE_MEMBERSHIP_STATUSES),
            )
        ).all()

        for membership in memberships:
            if required_product and membership.whop_product_id != required_product:
                continue

            organization = database.get(
                Organization,
                membership.organization_id,
            )

            if organization is not None and organization.status == "active":
                return OrganizationContext(
                    organization.id,
                    user.id,
                    membership.role,
                )

    raise HTTPException(403, "No active organization membership was found.")
