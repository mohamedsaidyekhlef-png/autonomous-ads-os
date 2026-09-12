import httpx
import pytest

from app.integrations.ats.base import (
    ATSAdapterError,
    schema_fingerprint,
)
from app.integrations.ats.greenhouse import GreenhouseAdapter
from app.integrations.ats.lever import LeverAdapter


def client_for(payload: object) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json=payload,
            request=request,
        )

    return httpx.Client(transport=httpx.MockTransport(handler))


def test_greenhouse_normalizes_public_jobs() -> None:
    payload = {
        "jobs": [
            {
                "id": 123,
                "title": "Senior Product Manager",
                "absolute_url": ("https://boards.greenhouse.io/acme/jobs/123"),
                "location": {"name": "Remote - US"},
                "departments": [{"name": "Product"}],
                "content": "<p>Lead product strategy.</p>",
                "updated_at": "2026-09-12T10:00:00Z",
            }
        ]
    }

    with client_for(payload) as client:
        snapshot = GreenhouseAdapter().fetch(
            "acme",
            client=client,
        )

    assert snapshot.provider == "greenhouse"
    assert snapshot.adapter_version == "greenhouse-job-board-v1"
    assert snapshot.posting_count == 1
    assert snapshot.postings[0].external_id == "123"
    assert snapshot.postings[0].title == "Senior Product Manager"
    assert snapshot.postings[0].location == "Remote - US"
    assert snapshot.postings[0].team == "Product"
    assert snapshot.postings[0].description_text == ("Lead product strategy.")


def test_lever_normalizes_public_jobs() -> None:
    payload = [
        {
            "id": "lever-123",
            "text": "Platform Engineer",
            "hostedUrl": ("https://jobs.lever.co/acme/lever-123"),
            "applyUrl": ("https://jobs.lever.co/acme/lever-123/apply"),
            "categories": {
                "location": "London",
                "team": "Engineering",
                "commitment": "Full-time",
            },
            "descriptionPlain": "Build reliable platforms.",
        }
    ]

    with client_for(payload) as client:
        snapshot = LeverAdapter().fetch(
            "acme",
            client=client,
        )

    assert snapshot.provider == "lever"
    assert snapshot.adapter_version == "lever-postings-v0"
    assert snapshot.posting_count == 1
    assert snapshot.postings[0].external_id == "lever-123"
    assert snapshot.postings[0].location == "London"
    assert snapshot.postings[0].team == "Engineering"
    assert snapshot.postings[0].employment_type == "Full-time"
    assert snapshot.postings[0].apply_url.endswith("/apply")


def test_schema_fingerprint_ignores_value_changes() -> None:
    first = {
        "jobs": [
            {
                "id": 1,
                "title": "Engineer",
                "location": {"name": "London"},
            }
        ]
    }
    second = {
        "jobs": [
            {
                "id": 2,
                "title": "Designer",
                "location": {"name": "Paris"},
            }
        ]
    }

    assert schema_fingerprint(first) == schema_fingerprint(second)


def test_schema_fingerprint_detects_structure_changes() -> None:
    first = {"jobs": [{"id": 1, "title": "Engineer"}]}
    second = {
        "jobs": [
            {
                "id": 1,
                "title": "Engineer",
                "department": "Technology",
            }
        ]
    }

    assert schema_fingerprint(first) != schema_fingerprint(second)


def test_adapter_rejects_unsafe_board_token() -> None:
    with pytest.raises(ATSAdapterError) as error:
        GreenhouseAdapter().fetch("../../example")

    assert error.value.code == "invalid_board_token"


def test_adapter_rejects_invalid_provider_schema() -> None:
    with (
        client_for({"unexpected": []}) as client,
        pytest.raises(ATSAdapterError) as error,
    ):
        GreenhouseAdapter().fetch(
            "acme",
            client=client,
        )

    assert error.value.code == "invalid_provider_schema"
