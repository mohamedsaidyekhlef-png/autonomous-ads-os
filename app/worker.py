"""Dedicated command worker process."""

import logging

from app.api.command_center import process_run
from app.workflows.queue import dequeue_run

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("command worker started")
    while True:
        try:
            run_id = dequeue_run()
            if run_id:
                process_run(run_id)
        except Exception:
            logger.exception("worker loop error")


if __name__ == "__main__":
    main()
