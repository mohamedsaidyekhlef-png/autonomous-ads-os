from app.workflows import queue


def test_queue_uses_durable_list(monkeypatch) -> None:
    calls = []

    class Redis:
        def lrem(self, key, count, value):
            calls.append(("lrem", key, count, value))
            return 0

        def lpush(self, key, value):
            calls.append(("lpush", key, value))
            return 1

    monkeypatch.setattr(queue, "get_redis", lambda: Redis())

    run_id = "00000000-0000-0000-0000-000000000001"
    queue.enqueue_run(run_id)

    assert calls == [
        ("lrem", queue.COMMAND_QUEUE, 0, run_id),
        ("lpush", queue.COMMAND_QUEUE, run_id),
    ]
