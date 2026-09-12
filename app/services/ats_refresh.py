from dataclasses import dataclass

import httpx
from sqlalchemy.orm import Session

from app.database.models.career import ATSBoard
from app.integrations.ats import ATSAdapterError, get_ats_adapter
from app.services.ats_coverage import (
    HealthObservation,
    record_health_observation,
)
from app.services.canonical_jobs import ingest_board_snapshot


@dataclass(frozen=True)
class RefreshResult:
    successful: bool
    board_state: str
    posting_count: int
    schema_hash: str | None
    schema_changed: bool
    adapter_version: str | None
    persisted_postings: int
    created_canonical_jobs: int
    deactivated_postings: int
    error_code: str | None
    error_message: str | None


def refresh_board(
    database: Session,
    board: ATSBoard,
    *,
    client: httpx.Client | None = None,
) -> RefreshResult:
    try:
        adapter = get_ats_adapter(board.provider)
        snapshot = adapter.fetch(
            board.board_token,
            client=client,
        )

        health = record_health_observation(
            database,
            board,
            HealthObservation(
                successful=True,
                http_status=snapshot.http_status,
                posting_count=snapshot.posting_count,
                schema_hash=snapshot.schema_hash,
            ),
        )

        ingestion = ingest_board_snapshot(
            database,
            board,
            snapshot,
        )

        board.board_metadata = {
            **board.board_metadata,
            "adapter_version": snapshot.adapter_version,
            "response_bytes": snapshot.response_bytes,
            "normalized_postings": (ingestion.observed_postings),
        }

        database.flush()

        return RefreshResult(
            successful=True,
            board_state=board.state,
            posting_count=board.posting_count,
            schema_hash=board.schema_hash,
            schema_changed=health.schema_changed,
            adapter_version=snapshot.adapter_version,
            persisted_postings=ingestion.observed_postings,
            created_canonical_jobs=(ingestion.created_canonical_jobs),
            deactivated_postings=(ingestion.deactivated_sources),
            error_code=None,
            error_message=None,
        )
    except ATSAdapterError as exc:
        record_health_observation(
            database,
            board,
            HealthObservation(
                successful=False,
                http_status=exc.http_status,
                error_code=exc.code,
                error_message=str(exc)[:1000],
            ),
        )

        database.flush()

        return RefreshResult(
            successful=False,
            board_state=board.state,
            posting_count=board.posting_count,
            schema_hash=board.schema_hash,
            schema_changed=False,
            adapter_version=None,
            persisted_postings=0,
            created_canonical_jobs=0,
            deactivated_postings=0,
            error_code=exc.code,
            error_message=str(exc),
        )
