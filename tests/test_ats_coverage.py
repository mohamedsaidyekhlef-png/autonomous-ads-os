from datetime import UTC, datetime

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.models.career import (
    ATSBoard,
    ATSBoardHealthCheck,
    ATSDriftAlert,
)
from app.services.ats_coverage import (
    DEAD_FAILURE_THRESHOLD,
    HealthObservation,
    record_health_observation,
)


def database_session() -> Session:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def board() -> ATSBoard:
    return ATSBoard(
        employer_name="Example Corp",
        employer_domain="example.com",
        provider="greenhouse",
        board_token="example",
        board_url="https://boards.greenhouse.io/example",
        source_method="manual",
        state="discovered",
        posting_count=0,
        consecutive_failures=0,
        board_metadata={},
    )


def test_success_advances_discovered_to_validated_then_live() -> None:
    with database_session() as database:
        item = board()
        database.add(item)
        database.flush()

        record_health_observation(
            database,
            item,
            HealthObservation(
                successful=True,
                http_status=200,
                posting_count=12,
                schema_hash="schema-v1",
                checked_at=datetime.now(UTC),
            ),
        )
        assert item.state == "validated"
        assert item.posting_count == 12

        record_health_observation(
            database,
            item,
            HealthObservation(
                successful=True,
                http_status=200,
                posting_count=13,
                schema_hash="schema-v1",
                checked_at=datetime.now(UTC),
            ),
        )
        assert item.state == "live"
        assert item.posting_count == 13

        checks = database.scalars(select(ATSBoardHealthCheck)).all()
        assert len(checks) == 2


def test_schema_change_degrades_board_and_opens_alert() -> None:
    with database_session() as database:
        item = board()
        item.state = "live"
        item.schema_hash = "schema-v1"
        database.add(item)
        database.flush()

        observation = record_health_observation(
            database,
            item,
            HealthObservation(
                successful=True,
                http_status=200,
                posting_count=10,
                schema_hash="schema-v2",
                checked_at=datetime.now(UTC),
            ),
        )

        assert observation.schema_changed is True
        assert item.state == "degraded"

        alert = database.scalars(select(ATSDriftAlert)).one()
        assert alert.status == "open"
        assert alert.previous_schema_hash == "schema-v1"
        assert alert.observed_schema_hash == "schema-v2"


def test_repeated_failures_mark_board_dead() -> None:
    with database_session() as database:
        item = board()
        item.state = "live"
        database.add(item)
        database.flush()

        for _ in range(DEAD_FAILURE_THRESHOLD):
            record_health_observation(
                database,
                item,
                HealthObservation(
                    successful=False,
                    http_status=503,
                    error_code="upstream_unavailable",
                    checked_at=datetime.now(UTC),
                ),
            )

        assert item.state == "dead"
        assert item.consecutive_failures == DEAD_FAILURE_THRESHOLD
