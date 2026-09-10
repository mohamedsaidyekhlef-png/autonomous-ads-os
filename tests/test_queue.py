from app.workflows import queue


def test_queue_uses_durable_list(monkeypatch) -> None:
    calls = []

    class Redis:
        def lpush(self, key, value):
            calls.append((key, value))

    monkeypatch.setattr(queue, "get_redis", lambda: Redis())
    queue.enqueue_run("00000000-0000-0000-0000-000000000001")
    assert calls == [(queue.COMMAND_QUEUE, "00000000-0000-0000-0000-000000000001")]
