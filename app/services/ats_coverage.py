from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.database.models.career import (
    ATSBoard,
    ATSBoardHealthCheck,
    ATSDriftAlert,
)

LIVE_REFRESH_INTERVAL = timedelta(hours=6)
DEGRADED_RETRY_INTERVAL = timedelta(hours=1)
DEAD_RETRY_INTERVAL = timedelta(days=1)
DEAD_FAILURE_THRESHOLD = 5

VALID_STATES = {
    "discovered",
    "validated",
    "live",
    "degraded",
    "dead",
}


@dataclass(frozen=True)
class HealthObservation:
    successful: bool
    http_status: int | None = None
    posting_count: int | None = None
    schema_hash: str | None = None
    duration_ms: int | None = None
    error_code: str | None = None
    error_message: str | None = None
    checked_at: datetime | None = None


def record_health_observation(
    database: Session,
    board: ATSBoard,
    observation: HealthObservation,
) -> ATSBoardHealthCheck:
    """Persist one observation and advance the board state machine."""

    checked_at = observation.checked_at or datetime.now(UTC)
    previous_hash = board.schema_hash

    schema_changed = bool(
        observation.successful
        and previous_hash
        and observation.schema_hash
        and previous_hash != observation.schema_hash
    )

    health = ATSBoardHealthCheck(
        board_id=board.id,
        checked_at=checked_at,
        successful=observation.successful,
        http_status=observation.http_status,
        posting_count=observation.posting_count,
        schema_hash=observation.schema_hash,
        schema_changed=schema_changed,
        duration_ms=observation.duration_ms,
        error_code=observation.error_code,
        error_message=observation.error_message,
    )
    database.add(health)

    board.last_checked_at = checked_at

    if observation.successful:
        board.consecutive_failures = 0
        board.last_successful_fetch_at = checked_at

        if observation.posting_count is not None:
            board.posting_count = max(0, observation.posting_count)

        if schema_changed:
            board.state = "degraded"
            board.next_check_at = checked_at + DEGRADED_RETRY_INTERVAL

            database.add(
                ATSDriftAlert(
                    board_id=board.id,
                    status="open",
                    detected_at=checked_at,
                    previous_schema_hash=previous_hash,
                    observed_schema_hash=observation.schema_hash or "",
                    details={
                        "provider": board.provider,
                        "board_url": board.board_url,
                        "reason": "schema_hash_changed",
                    },
                )
            )
        else:
            if board.state == "discovered":
                board.state = "validated"
            else:
                board.state = "live"

            board.next_check_at = checked_at + LIVE_REFRESH_INTERVAL

        if observation.schema_hash:
            board.schema_hash = observation.schema_hash
    else:
        board.consecutive_failures += 1

        if board.consecutive_failures >= DEAD_FAILURE_THRESHOLD:
            board.state = "dead"
            board.next_check_at = checked_at + DEAD_RETRY_INTERVAL
        elif board.state != "discovered":
            board.state = "degraded"
            board.next_check_at = checked_at + DEGRADED_RETRY_INTERVAL
        else:
            board.next_check_at = checked_at + DEGRADED_RETRY_INTERVAL

    database.flush()
    return health
