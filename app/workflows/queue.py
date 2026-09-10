"""Crash-safe Redis queue for command runs."""

import time
import uuid

from redis import Redis
from redis.exceptions import RedisError

from app.core.settings import get_settings

COMMAND_QUEUE = "ads_os:command_runs:queued"
PROCESSING_QUEUE = "ads_os:command_runs:processing"
CLAIMED_AT = "ads_os:command_runs:claimed_at"
RETRY_COUNTS = "ads_os:command_runs:retries"

MAX_RETRIES = 3
STALE_AFTER_SECONDS = 900


def get_redis() -> Redis:
    return Redis.from_url(
        get_settings().redis_url,
        decode_responses=True,
    )


def enqueue_run(run_id: uuid.UUID | str) -> None:
    value = str(run_id)

    try:
        client = get_redis()
        client.lrem(COMMAND_QUEUE, 0, value)
        client.lpush(COMMAND_QUEUE, value)
    except RedisError as exc:
        raise RuntimeError("Command queue is unavailable.") from exc


def claim_run(timeout_seconds: int = 5) -> uuid.UUID | None:
    """Atomically move one job from queued to processing."""

    try:
        client = get_redis()
        value = client.brpoplpush(
            COMMAND_QUEUE,
            PROCESSING_QUEUE,
            timeout=timeout_seconds,
        )

        if value is None:
            return None

        client.zadd(CLAIMED_AT, {value: time.time()})
        return uuid.UUID(value)
    except (RedisError, ValueError) as exc:
        raise RuntimeError("Command queue is unavailable.") from exc


def dequeue_run(timeout_seconds: int = 5) -> uuid.UUID | None:
    """Compatibility alias for the crash-safe claim operation."""

    return claim_run(timeout_seconds)


def acknowledge_run(run_id: uuid.UUID | str) -> None:
    value = str(run_id)

    try:
        client = get_redis()
        client.lrem(PROCESSING_QUEUE, 0, value)
        client.zrem(CLAIMED_AT, value)
        client.hdel(RETRY_COUNTS, value)
    except RedisError as exc:
        raise RuntimeError("Could not acknowledge command run.") from exc


def retry_run(
    run_id: uuid.UUID | str,
    max_retries: int = MAX_RETRIES,
) -> bool:
    """Requeue a claimed job if its retry budget remains."""

    value = str(run_id)

    try:
        client = get_redis()
        attempts = int(client.hincrby(RETRY_COUNTS, value, 1))
        client.lrem(PROCESSING_QUEUE, 0, value)
        client.zrem(CLAIMED_AT, value)

        if attempts <= max_retries:
            client.lpush(COMMAND_QUEUE, value)
            return True

        client.hdel(RETRY_COUNTS, value)
        return False
    except RedisError as exc:
        raise RuntimeError("Could not retry command run.") from exc


def recover_stale_jobs(
    stale_after_seconds: int = STALE_AFTER_SECONDS,
) -> list[uuid.UUID]:
    """Return abandoned processing jobs to the queued list."""

    cutoff = time.time() - stale_after_seconds
    recovered: list[uuid.UUID] = []

    try:
        client = get_redis()
        values = client.zrangebyscore(CLAIMED_AT, 0, cutoff)

        for value in values:
            removed = client.lrem(PROCESSING_QUEUE, 1, value)
            client.zrem(CLAIMED_AT, value)

            if removed:
                client.lpush(COMMAND_QUEUE, value)
                recovered.append(uuid.UUID(value))

        return recovered
    except (RedisError, ValueError) as exc:
        raise RuntimeError("Could not recover stale command runs.") from exc


def cancel_queued_run(run_id: uuid.UUID | str) -> bool:
    value = str(run_id)

    try:
        removed = get_redis().lrem(COMMAND_QUEUE, 0, value)
        return bool(removed)
    except RedisError as exc:
        raise RuntimeError("Could not cancel queued command run.") from exc
