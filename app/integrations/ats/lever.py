from html.parser import HTMLParser
from io import StringIO
from typing import Any

import httpx

from app.integrations.ats.base import (
    ATSAdapterError,
    BoardSnapshot,
    NormalizedPosting,
    parse_json_response,
    schema_fingerprint,
    validate_board_token,
)

USER_AGENT = "AutonomousCareerOS/0.1 ATSCoverageHealth"
ENDPOINT = "https://api.lever.co/v0/postings/{token}"


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.output = StringIO()

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if value:
            self.output.write(value)
            self.output.write(" ")

    def text(self) -> str:
        return " ".join(self.output.getvalue().split())


def html_to_text(value: Any) -> str:
    if not isinstance(value, str) or not value:
        return ""

    parser = _TextExtractor()
    parser.feed(value)
    parser.close()
    return parser.text()


def optional_string(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value.strip()
    return None


class LeverAdapter:
    provider = "lever"
    version = "lever-postings-v0"

    def fetch(
        self,
        board_token: str,
        *,
        client: httpx.Client | None = None,
    ) -> BoardSnapshot:
        token = validate_board_token(board_token)
        url = ENDPOINT.format(token=token)

        if client is not None:
            return self._fetch(client, token, url)

        try:
            with httpx.Client(
                timeout=20,
                follow_redirects=False,
                headers={
                    "Accept": "application/json",
                    "User-Agent": USER_AGENT,
                },
            ) as managed_client:
                return self._fetch(managed_client, token, url)
        except httpx.HTTPError as exc:
            raise ATSAdapterError(
                "The Lever board could not be reached.",
                code="provider_network_error",
            ) from exc

    def _fetch(
        self,
        client: httpx.Client,
        token: str,
        url: str,
    ) -> BoardSnapshot:
        try:
            response = client.get(
                url,
                params={"mode": "json"},
                headers={
                    "Accept": "application/json",
                    "User-Agent": USER_AGENT,
                },
            )
        except httpx.HTTPError as exc:
            raise ATSAdapterError(
                "The Lever board could not be reached.",
                code="provider_network_error",
            ) from exc

        payload = parse_json_response(response)

        if not isinstance(payload, list):
            raise ATSAdapterError(
                "The Lever response must be a JSON array.",
                code="invalid_provider_schema",
                http_status=response.status_code,
            )

        postings: list[NormalizedPosting] = []

        for raw_job in payload:
            if not isinstance(raw_job, dict):
                continue

            external_id = str(raw_job.get("id") or "").strip()
            title = str(raw_job.get("text") or "").strip()
            hosted_url = str(raw_job.get("hostedUrl") or "").strip()
            apply_url = str(raw_job.get("applyUrl") or hosted_url).strip()

            if not external_id or not title or not hosted_url:
                continue

            categories = raw_job.get("categories")
            location = None
            team = None
            employment_type = None

            if isinstance(categories, dict):
                location = optional_string(categories.get("location"))
                team = optional_string(categories.get("team"))
                employment_type = optional_string(categories.get("commitment"))

            description = raw_job.get("descriptionPlain")

            if not isinstance(description, str):
                description = html_to_text(raw_job.get("description"))

            postings.append(
                NormalizedPosting(
                    external_id=external_id,
                    title=title,
                    location=location,
                    team=team,
                    employment_type=employment_type,
                    description_text=description.strip(),
                    source_url=hosted_url,
                    apply_url=apply_url,
                    updated_at=None,
                )
            )

        return BoardSnapshot(
            provider=self.provider,
            adapter_version=self.version,
            board_token=token,
            source_url=url,
            posting_count=len(postings),
            schema_hash=schema_fingerprint(payload),
            postings=tuple(postings),
            http_status=response.status_code,
            response_bytes=len(response.content),
        )
