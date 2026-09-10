"""Redis-backed durable queue for command runs."""

import uuid

from redis import Redis
from redis.exceptions import RedisError

from app.core.settings import get_settings

COMMAND_QUEUE = "ads_os:command_runs"


def get_redis() -> Redis:
    return Redis.from_url(get_settings().redis_url, decode_responses=True)


def enqueue_run(run_id: uuid.UUID) -> None:
    try:
        get_redis().lpush(COMMAND_QUEUE, str(run_id))
    except RedisError as exc:
        raise RuntimeError("Command queue is unavailable.") from exc


def dequeue_run(timeout_seconds: int = 5) -> uuid.UUID | None:
    try:
        item = get_redis().brpop(COMMAND_QUEUE, timeout=timeout_seconds)
    except RedisError as exc:
        raise RuntimeError("Command queue is unavailable.") from exc
    return uuid.UUID(item[1]) if item else None
