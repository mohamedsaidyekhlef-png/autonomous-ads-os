"""Dedicated crash-safe command worker process."""

import logging
import time
import uuid
from datetime import UTC, datetime

from app.api.command_center import process_run
from app.database.models import AgentRun
from app.database.session import SessionLocal
from app.workflows.queue import (
    acknowledge_run,
    claim_run,
    recover_stale_jobs,
    retry_run,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _reset_recovered_runs(run_ids: list[uuid.UUID]) -> None:
    if not run_ids:
        return

    with SessionLocal() as database:
        for run_id in run_ids:
            run = database.get(AgentRun, run_id)

            if run is not None and run.status == "running":
                run.status = "queued"
                run.started_at = None
                run.error_message = None

        database.commit()


def _mark_permanently_failed(run_id: uuid.UUID) -> None:
    with SessionLocal() as database:
        run = database.get(AgentRun, run_id)

        if run is not None and run.status not in {
            "completed",
            "failed",
            "cancelled",
        }:
            run.status = "failed"
            run.error_message = "Worker retry limit was reached."
            run.completed_at = datetime.now(UTC)
            database.commit()


def main() -> None:
    logger.info("command worker started")
    last_recovery = 0.0

    while True:
        try:
            now = time.monotonic()

            if now - last_recovery >= 60:
                recovered = recover_stale_jobs()
                _reset_recovered_runs(recovered)
                last_recovery = now

            run_id = claim_run()

            if run_id is None:
                continue

            try:
                process_run(run_id)
            except Exception:
                logger.exception("command run failed unexpectedly: %s", run_id)

                if retry_run(run_id):
                    _reset_recovered_runs([run_id])
                else:
                    _mark_permanently_failed(run_id)
            else:
                acknowledge_run(run_id)

        except Exception:
            logger.exception("worker loop error")
            time.sleep(2)


if __name__ == "__main__":
    main()
