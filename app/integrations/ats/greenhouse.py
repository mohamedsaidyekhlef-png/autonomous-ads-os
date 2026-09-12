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
ENDPOINT = "https://boards-api.greenhouse.io/v1/boards/{token}/jobs"


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


class GreenhouseAdapter:
    provider = "greenhouse"
    version = "greenhouse-job-board-v1"

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
                "The Greenhouse board could not be reached.",
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
                params={"content": "true"},
                headers={
                    "Accept": "application/json",
                    "User-Agent": USER_AGENT,
                },
            )
        except httpx.HTTPError as exc:
            raise ATSAdapterError(
                "The Greenhouse board could not be reached.",
                code="provider_network_error",
            ) from exc

        payload = parse_json_response(response)

        if not isinstance(payload, dict):
            raise ATSAdapterError(
                "The Greenhouse response must be a JSON object.",
                code="invalid_provider_schema",
                http_status=response.status_code,
            )

        raw_jobs = payload.get("jobs")

        if not isinstance(raw_jobs, list):
            raise ATSAdapterError(
                "The Greenhouse response contains no jobs collection.",
                code="invalid_provider_schema",
                http_status=response.status_code,
            )

        postings: list[NormalizedPosting] = []

        for raw_job in raw_jobs:
            if not isinstance(raw_job, dict):
                continue

            external_id = str(raw_job.get("id") or "").strip()
            title = str(raw_job.get("title") or "").strip()
            absolute_url = str(raw_job.get("absolute_url") or "").strip()

            if not external_id or not title or not absolute_url:
                continue

            location_value = raw_job.get("location")
            location = None

            if isinstance(location_value, dict):
                location = optional_string(location_value.get("name"))

            departments = raw_job.get("departments")
            team = None

            if isinstance(departments, list):
                names = [
                    str(item.get("name")).strip()
                    for item in departments
                    if isinstance(item, dict) and item.get("name")
                ]
                team = ", ".join(names) or None

            postings.append(
                NormalizedPosting(
                    external_id=external_id,
                    title=title,
                    location=location,
                    team=team,
                    employment_type=None,
                    description_text=html_to_text(raw_job.get("content")),
                    source_url=absolute_url,
                    apply_url=absolute_url,
                    updated_at=optional_string(raw_job.get("updated_at")),
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
