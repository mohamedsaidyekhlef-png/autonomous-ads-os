import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from app.core.settings import get_settings
from app.core.token_vault import TokenVault, TokenVaultError
from app.database.models.saas import (
    AdvertisingAccount,
    OAuthCredential,
    Organization,
    PlatformConnection,
)
from app.database.session import SessionLocal

router = APIRouter(prefix="/oauth", tags=["OAuth"])

GOOGLE_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_ADS_API_ROOT = "https://googleads.googleapis.com"

GOOGLE_SCOPES = (
    "openid",
    "email",
    "https://www.googleapis.com/auth/adwords",
)

STATE_MAX_AGE_SECONDS = 600
GOOGLE_ADS_API_VERSION = "v25"
DASHBOARD_URL = "http://localhost:3000"


def secret_value(value: Any) -> str:
    if value is None:
        return ""

    getter = getattr(value, "get_secret_value", None)
    if callable(getter):
        return str(getter())

    return str(value)


def oauth_serializer() -> URLSafeTimedSerializer:
    settings = get_settings()
    application_secret = secret_value(settings.app_secret_key)

    if not application_secret:
        raise HTTPException(
            status_code=503,
            detail="APP_SECRET_KEY is not configured.",
        )

    return URLSafeTimedSerializer(
        secret_key=application_secret,
        salt="google-oauth-state-v1",
    )


def google_configuration() -> dict[str, str]:
    settings = get_settings()

    configuration = {
        "client_id": secret_value(settings.google_client_id),
        "client_secret": secret_value(settings.google_client_secret),
        "redirect_uri": secret_value(settings.google_redirect_uri),
        "developer_token": secret_value(settings.google_ads_developer_token),
        "manager_customer_id": secret_value(
            settings.google_ads_manager_customer_id
        ).replace("-", ""),
    }

    required = (
        "client_id",
        "client_secret",
        "redirect_uri",
        "developer_token",
    )
    missing = [name for name in required if not configuration[name]]

    if missing:
        raise HTTPException(
            status_code=503,
            detail={
                "status": "configuration_required",
                "platform": "google_ads",
                "missing": missing,
                "message": (
                    "Google Ads OAuth is not completely configured. "
                    "Add the missing application credentials to .env."
                ),
            },
        )

    return configuration


def get_development_organization(
    organization_id: uuid.UUID | None,
) -> Organization:
    settings = get_settings()

    with SessionLocal() as database:
        if organization_id is not None:
            organization = database.get(Organization, organization_id)

            if organization is None:
                raise HTTPException(
                    status_code=404,
                    detail="Organization was not found.",
                )

            database.expunge(organization)
            return organization

        if settings.app_env != "development":
            raise HTTPException(
                status_code=401,
                detail=(
                    "An authenticated organization context is required "
                    "outside development mode."
                ),
            )

        organization = database.scalars(
            select(Organization)
            .where(Organization.status == "active")
            .order_by(Organization.created_at)
            .limit(1)
        ).first()

        if organization is None:
            organization = Organization(
                name="Development Organization",
                status="active",
                automation_enabled=False,
                risk_profile="conservative",
                daily_spend_cap_minor=0,
                monthly_spend_cap_minor=0,
                currency="USD",
            )
            database.add(organization)
            database.commit()
            database.refresh(organization)

        database.expunge(organization)
        return organization


async def store_single_use_state(nonce: str) -> None:
    settings = get_settings()
    redis_client = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

    try:
        stored = await redis_client.set(
            f"oauth:google:{nonce}",
            "unused",
            ex=STATE_MAX_AGE_SECONDS,
            nx=True,
        )

        if not stored:
            raise HTTPException(
                status_code=503,
                detail="Could not establish a unique OAuth state.",
            )
    except RedisError as exc:
        raise HTTPException(
            status_code=503,
            detail="OAuth state storage is unavailable.",
        ) from exc
    finally:
        await redis_client.aclose()


async def consume_single_use_state(nonce: str) -> None:
    settings = get_settings()
    redis_client = Redis.from_url(
        settings.redis_url,
        decode_responses=True,
    )

    try:
        stored_value = await redis_client.getdel(f"oauth:google:{nonce}")

        if stored_value != "unused":
            raise HTTPException(
                status_code=400,
                detail="OAuth state is invalid, expired, or already used.",
            )
    except RedisError as exc:
        raise HTTPException(
            status_code=503,
            detail="OAuth state validation is unavailable.",
        ) from exc
    finally:
        await redis_client.aclose()


async def exchange_google_code(
    code: str,
    configuration: dict[str, str],
) -> dict[str, Any]:
    payload = {
        "code": code,
        "client_id": configuration["client_id"],
        "client_secret": configuration["client_secret"],
        "redirect_uri": configuration["redirect_uri"],
        "grant_type": "authorization_code",
    }

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                GOOGLE_TOKEN_URL,
                data=payload,
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            token_data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Google rejected the OAuth token exchange.",
        ) from exc

    access_token = token_data.get("access_token")

    if not isinstance(access_token, str) or not access_token:
        raise HTTPException(
            status_code=502,
            detail="Google did not return an access token.",
        )

    return token_data


async def fetch_google_identity(access_token: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                GOOGLE_USERINFO_URL,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/json",
                },
            )
            response.raise_for_status()
            identity = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Google identity verification failed.",
        ) from exc

    external_user_id = identity.get("sub")

    if not isinstance(external_user_id, str) or not external_user_id:
        raise HTTPException(
            status_code=502,
            detail="Google did not return a stable user identifier.",
        )

    return identity


def google_ads_headers(
    access_token: str,
    configuration: dict[str, str],
    include_manager: bool = False,
) -> dict[str, str]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "developer-token": configuration["developer_token"],
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    if include_manager and configuration["manager_customer_id"]:
        headers["login-customer-id"] = configuration["manager_customer_id"]

    return headers


async def fetch_customer_metadata(
    client: httpx.AsyncClient,
    customer_id: str,
    access_token: str,
    configuration: dict[str, str],
) -> dict[str, Any]:
    endpoint = (
        f"{GOOGLE_ADS_API_ROOT}/{GOOGLE_ADS_API_VERSION}"
        f"/customers/{customer_id}/googleAds:search"
    )

    query = """
        SELECT
          customer.id,
          customer.descriptive_name,
          customer.currency_code,
          customer.time_zone,
          customer.status,
          customer.manager
        FROM customer
        LIMIT 1
    """

    try:
        response = await client.post(
            endpoint,
            headers=google_ads_headers(
                access_token,
                configuration,
                include_manager=True,
            ),
            json={"query": query},
        )
        response.raise_for_status()
        payload = response.json()

        results = payload.get("results", [])
        customer = results[0].get("customer", {}) if results else {}

        return {
            "external_account_id": str(customer.get("id", customer_id)),
            "name": customer.get(
                "descriptiveName",
                f"Google Ads {customer_id}",
            ),
            "currency": customer.get("currencyCode"),
            "timezone_name": customer.get("timeZone"),
            "status": str(customer.get("status", "accessible")).lower(),
            "is_manager": bool(customer.get("manager", False)),
        }
    except (httpx.HTTPError, ValueError, IndexError, AttributeError):
        return {
            "external_account_id": customer_id,
            "name": f"Google Ads {customer_id}",
            "currency": None,
            "timezone_name": None,
            "status": "accessible",
            "is_manager": False,
        }


async def discover_google_ads_accounts(
    access_token: str,
    configuration: dict[str, str],
) -> list[dict[str, Any]]:
    endpoint = (
        f"{GOOGLE_ADS_API_ROOT}/{GOOGLE_ADS_API_VERSION}"
        "/customers:listAccessibleCustomers"
    )

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.get(
                endpoint,
                headers=google_ads_headers(
                    access_token,
                    configuration,
                ),
            )
            response.raise_for_status()
            payload = response.json()

            resource_names = payload.get("resourceNames", [])
            accounts: list[dict[str, Any]] = []

            for resource_name in resource_names:
                customer_id = str(resource_name).split("/")[-1]

                if not customer_id.isdigit():
                    continue

                metadata = await fetch_customer_metadata(
                    client,
                    customer_id,
                    access_token,
                    configuration,
                )
                accounts.append(metadata)

            return accounts
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail=(
                "Google authorization succeeded, but Google Ads account "
                "discovery failed. Verify the developer token and Ads access."
            ),
        ) from exc


def save_google_connection(
    organization_id: uuid.UUID,
    identity: dict[str, Any],
    token_data: dict[str, Any],
    accounts: list[dict[str, Any]],
    configuration: dict[str, str],
) -> tuple[PlatformConnection, int]:
    vault = TokenVault()
    external_user_id = str(identity["sub"])
    access_token = str(token_data["access_token"])
    refresh_token = token_data.get("refresh_token")
    expires_in = int(token_data.get("expires_in", 3600))
    expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)
    scopes = str(token_data.get("scope", "")).split()
    now = datetime.now(UTC)

    try:
        with SessionLocal() as database:
            organization = database.get(
                Organization,
                organization_id,
            )

            if organization is None:
                raise HTTPException(
                    status_code=404,
                    detail="Organization was not found.",
                )

            connection = database.scalars(
                select(PlatformConnection).where(
                    PlatformConnection.organization_id == organization_id,
                    PlatformConnection.platform == "google_ads",
                    PlatformConnection.external_user_id == external_user_id,
                )
            ).one_or_none()

            connection_status = "connected" if accounts else "no_accounts"

            if connection is None:
                connection = PlatformConnection(
                    organization_id=organization_id,
                    platform="google_ads",
                    external_user_id=external_user_id,
                    status=connection_status,
                    granted_scopes=scopes,
                    token_expires_at=expires_at,
                    last_verified_at=now,
                )
                database.add(connection)
                database.flush()
            else:
                connection.status = connection_status
                connection.granted_scopes = scopes
                connection.token_expires_at = expires_at
                connection.last_verified_at = now

            credential = database.scalars(
                select(OAuthCredential).where(
                    OAuthCredential.platform_connection_id == connection.id
                )
            ).one_or_none()

            encrypted_access_token = vault.encrypt(access_token)

            if credential is None:
                encrypted_refresh_token = (
                    vault.encrypt(str(refresh_token)) if refresh_token else None
                )

                credential = OAuthCredential(
                    platform_connection_id=connection.id,
                    encrypted_access_token=encrypted_access_token,
                    encrypted_refresh_token=encrypted_refresh_token,
                    token_type=str(token_data.get("token_type", "Bearer")),
                    access_token_expires_at=expires_at,
                    refresh_token_expires_at=None,
                    encryption_key_version="local-v1",
                )
                database.add(credential)
            else:
                credential.encrypted_access_token = encrypted_access_token

                if refresh_token:
                    credential.encrypted_refresh_token = vault.encrypt(
                        str(refresh_token)
                    )

                credential.token_type = str(token_data.get("token_type", "Bearer"))
                credential.access_token_expires_at = expires_at
                credential.encryption_key_version = "local-v1"

            saved_accounts = 0

            for discovered in accounts:
                external_account_id = discovered["external_account_id"]

                account = database.scalars(
                    select(AdvertisingAccount).where(
                        AdvertisingAccount.platform == "google_ads",
                        AdvertisingAccount.external_account_id == external_account_id,
                    )
                ).one_or_none()

                if account is not None and account.organization_id != organization_id:
                    continue

                if account is None:
                    account = AdvertisingAccount(
                        organization_id=organization_id,
                        platform_connection_id=connection.id,
                        platform="google_ads",
                        external_account_id=external_account_id,
                        external_manager_id=(
                            configuration["manager_customer_id"] or None
                        ),
                        name=discovered["name"],
                        currency=discovered["currency"],
                        timezone_name=discovered["timezone_name"],
                        status=discovered["status"],
                        automation_enabled=False,
                        capabilities={
                            "read": True,
                            "write": False,
                            "is_manager": discovered["is_manager"],
                            "shadow_mode": True,
                        },
                    )
                    database.add(account)
                else:
                    account.platform_connection_id = connection.id
                    account.name = discovered["name"]
                    account.currency = discovered["currency"]
                    account.timezone_name = discovered["timezone_name"]
                    account.status = discovered["status"]
                    account.capabilities = {
                        "read": True,
                        "write": account.automation_enabled,
                        "is_manager": discovered["is_manager"],
                        "shadow_mode": True,
                    }

                saved_accounts += 1

            database.commit()
            database.refresh(connection)
            database.expunge(connection)

            return connection, saved_accounts

    except (SQLAlchemyError, TokenVaultError) as exc:
        raise HTTPException(
            status_code=500,
            detail="The encrypted Google connection could not be saved.",
        ) from exc


@router.get("/google/start")
async def start_google_oauth(
    organization_id: uuid.UUID | None = None,
) -> RedirectResponse:
    configuration = google_configuration()
    organization = get_development_organization(organization_id)

    nonce = secrets.token_urlsafe(32)
    await store_single_use_state(nonce)

    state = oauth_serializer().dumps(
        {
            "organization_id": str(organization.id),
            "nonce": nonce,
            "platform": "google_ads",
        }
    )

    parameters = {
        "client_id": configuration["client_id"],
        "redirect_uri": configuration["redirect_uri"],
        "response_type": "code",
        "scope": " ".join(GOOGLE_SCOPES),
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }

    authorization_url = f"{GOOGLE_AUTHORIZATION_URL}?{urlencode(parameters)}"

    return RedirectResponse(
        authorization_url,
        status_code=302,
    )


@router.get("/google/callback")
async def google_oauth_callback(
    state: str,
    code: str | None = None,
    error: str | None = None,
) -> RedirectResponse:
    if error:
        return RedirectResponse(
            f"{DASHBOARD_URL}/connections?"
            + urlencode(
                {
                    "google": "error",
                    "message": error,
                }
            ),
            status_code=302,
        )

    if not code:
        raise HTTPException(
            status_code=400,
            detail="Google did not return an authorization code.",
        )

    try:
        state_payload = oauth_serializer().loads(
            state,
            max_age=STATE_MAX_AGE_SECONDS,
        )
    except SignatureExpired as exc:
        raise HTTPException(
            status_code=400,
            detail="OAuth authorization expired. Please try again.",
        ) from exc
    except BadSignature as exc:
        raise HTTPException(
            status_code=400,
            detail="OAuth state signature is invalid.",
        ) from exc

    if state_payload.get("platform") != "google_ads":
        raise HTTPException(
            status_code=400,
            detail="OAuth platform state is invalid.",
        )

    nonce = str(state_payload.get("nonce", ""))
    await consume_single_use_state(nonce)

    try:
        organization_id = uuid.UUID(str(state_payload["organization_id"]))
    except (ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=400,
            detail="OAuth organization state is invalid.",
        ) from exc

    configuration = google_configuration()
    token_data = await exchange_google_code(code, configuration)
    access_token = str(token_data["access_token"])

    identity = await fetch_google_identity(access_token)
    accounts = await discover_google_ads_accounts(
        access_token,
        configuration,
    )

    connection, account_count = save_google_connection(
        organization_id,
        identity,
        token_data,
        accounts,
        configuration,
    )

    query = urlencode(
        {
            "google": "connected",
            "accounts": account_count,
            "connection_id": str(connection.id),
        }
    )

    return RedirectResponse(
        f"{DASHBOARD_URL}/connections?{query}",
        status_code=302,
    )


@router.get("/google/status")
def google_connection_status(
    organization_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    organization = get_development_organization(organization_id)

    with SessionLocal() as database:
        connections = database.scalars(
            select(PlatformConnection).where(
                PlatformConnection.organization_id == organization.id,
                PlatformConnection.platform == "google_ads",
            )
        ).all()

        connection_ids = [connection.id for connection in connections]

        if not connection_ids:
            return {
                "platform": "google_ads",
                "connected": False,
                "connections": 0,
                "accounts": [],
            }

        accounts = database.scalars(
            select(AdvertisingAccount).where(
                AdvertisingAccount.organization_id == organization.id,
                AdvertisingAccount.platform == "google_ads",
                AdvertisingAccount.platform_connection_id.in_(connection_ids),
            )
        ).all()

        return {
            "platform": "google_ads",
            "connected": any(
                connection.status == "connected" for connection in connections
            ),
            "connections": len(connections),
            "accounts": [
                {
                    "id": str(account.id),
                    "customer_id": account.external_account_id,
                    "name": account.name,
                    "currency": account.currency,
                    "timezone": account.timezone_name,
                    "status": account.status,
                    "automation_enabled": (account.automation_enabled),
                }
                for account in accounts
            ],
        }
