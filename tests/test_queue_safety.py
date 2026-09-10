import uuid

from app.workflows import queue


class FakeRedis:
    def __init__(self) -> None:
        self.queued: list[str] = []
        self.processing: list[str] = []
        self.claimed: dict[str, float] = {}
        self.retries: dict[str, int] = {}

    def lpush(self, key: str, value: str) -> int:
        target = self.queued if key == queue.COMMAND_QUEUE else self.processing
        target.insert(0, value)
        return len(target)

    def lrem(self, key: str, _count: int, value: str) -> int:
        target = self.queued if key == queue.COMMAND_QUEUE else self.processing
        before = len(target)
        target[:] = [item for item in target if item != value]
        return before - len(target)

    def brpoplpush(
        self,
        _source: str,
        _destination: str,
        timeout: int,
    ) -> str | None:
        del timeout
        if not self.queued:
            return None
        value = self.queued.pop()
        self.processing.insert(0, value)
        return value

    def zadd(self, _key: str, mapping: dict[str, float]) -> int:
        self.claimed.update(mapping)
        return len(mapping)

    def zrem(self, _key: str, value: str) -> int:
        return int(self.claimed.pop(value, None) is not None)

    def zrangebyscore(
        self,
        _key: str,
        _minimum: float,
        maximum: float,
    ) -> list[str]:
        return [
            value for value, timestamp in self.claimed.items() if timestamp <= maximum
        ]

    def hincrby(self, _key: str, value: str, amount: int) -> int:
        self.retries[value] = self.retries.get(value, 0) + amount
        return self.retries[value]

    def hdel(self, _key: str, value: str) -> int:
        return int(self.retries.pop(value, None) is not None)


def test_claim_is_atomic_and_acknowledged(monkeypatch) -> None:
    redis = FakeRedis()
    monkeypatch.setattr(queue, "get_redis", lambda: redis)

    run_id = uuid.uuid4()
    queue.enqueue_run(run_id)

    claimed = queue.claim_run(timeout_seconds=0)

    assert claimed == run_id
    assert str(run_id) not in redis.queued
    assert str(run_id) in redis.processing
    assert str(run_id) in redis.claimed

    queue.acknowledge_run(run_id)

    assert str(run_id) not in redis.processing
    assert str(run_id) not in redis.claimed


def test_stale_claim_is_recovered(monkeypatch) -> None:
    redis = FakeRedis()
    monkeypatch.setattr(queue, "get_redis", lambda: redis)

    run_id = uuid.uuid4()
    value = str(run_id)
    redis.processing.append(value)
    redis.claimed[value] = 1.0

    recovered = queue.recover_stale_jobs(stale_after_seconds=1)

    assert recovered == [run_id]
    assert value in redis.queued
    assert value not in redis.processing


def test_retry_is_bounded(monkeypatch) -> None:
    redis = FakeRedis()
    monkeypatch.setattr(queue, "get_redis", lambda: redis)

    run_id = uuid.uuid4()
    value = str(run_id)

    for _attempt in range(3):
        redis.processing[:] = [value]
        assert queue.retry_run(run_id, max_retries=3)

    redis.processing[:] = [value]
    assert not queue.retry_run(run_id, max_retries=3)


def test_queued_run_can_be_cancelled(monkeypatch) -> None:
    redis = FakeRedis()
    monkeypatch.setattr(queue, "get_redis", lambda: redis)

    run_id = uuid.uuid4()
    queue.enqueue_run(run_id)

    assert queue.cancel_queued_run(run_id)
    assert not queue.cancel_queued_run(run_id)
