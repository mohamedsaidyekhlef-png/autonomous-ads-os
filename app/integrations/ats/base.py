import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

MAX_RESPONSE_BYTES = 10 * 1024 * 1024
BOARD_TOKEN_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,199}$")


class ATSAdapterError(RuntimeError):
    """Safe provider-adapter failure."""

    def __init__(
        self,
        message: str,
        *,
        code: str,
        http_status: int | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.http_status = http_status


@dataclass(frozen=True)
class NormalizedPosting:
    external_id: str
    title: str
    location: str | None
    team: str | None
    employment_type: str | None
    description_text: str
    source_url: str
    apply_url: str
    updated_at: str | None


@dataclass(frozen=True)
class BoardSnapshot:
    provider: str
    adapter_version: str
    board_token: str
    source_url: str
    posting_count: int
    schema_hash: str
    postings: tuple[NormalizedPosting, ...]
    http_status: int
    response_bytes: int


class ATSAdapter(Protocol):
    provider: str
    version: str

    def fetch(
        self,
        board_token: str,
        *,
        client: httpx.Client | None = None,
    ) -> BoardSnapshot: ...


def validate_board_token(board_token: str) -> str:
    token = board_token.strip()

    if not BOARD_TOKEN_PATTERN.fullmatch(token):
        raise ATSAdapterError(
            "The ATS board token contains unsupported characters.",
            code="invalid_board_token",
        )

    return token


def ensure_response_size(response: httpx.Response) -> None:
    content_length = response.headers.get("content-length")

    if content_length:
        try:
            declared_size = int(content_length)
        except ValueError:
            declared_size = 0

        if declared_size > MAX_RESPONSE_BYTES:
            raise ATSAdapterError(
                "The ATS response exceeded the maximum allowed size.",
                code="response_too_large",
                http_status=response.status_code,
            )

    if len(response.content) > MAX_RESPONSE_BYTES:
        raise ATSAdapterError(
            "The ATS response exceeded the maximum allowed size.",
            code="response_too_large",
            http_status=response.status_code,
        )


def parse_json_response(response: httpx.Response) -> Any:
    ensure_response_size(response)

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise ATSAdapterError(
            f"The ATS provider returned HTTP {response.status_code}.",
            code="provider_http_error",
            http_status=response.status_code,
        ) from exc

    try:
        return response.json()
    except ValueError as exc:
        raise ATSAdapterError(
            "The ATS provider returned invalid JSON.",
            code="invalid_provider_json",
            http_status=response.status_code,
        ) from exc


def _schema_shape(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _schema_shape(item) for key, item in sorted(value.items())}

    if isinstance(value, list):
        if not value:
            return ["empty"]

        unique_shapes: dict[str, Any] = {}

        for item in value[:25]:
            shape = _schema_shape(item)
            encoded = json.dumps(
                shape,
                sort_keys=True,
                separators=(",", ":"),
            )
            unique_shapes[encoded] = shape

        return [unique_shapes[key] for key in sorted(unique_shapes)]

    if value is None:
        return "null"

    if isinstance(value, bool):
        return "boolean"

    if isinstance(value, int):
        return "integer"

    if isinstance(value, float):
        return "number"

    if isinstance(value, str):
        return "string"

    return type(value).__name__


def schema_fingerprint(payload: Any) -> str:
    shape = _schema_shape(payload)
    encoded = json.dumps(
        shape,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
