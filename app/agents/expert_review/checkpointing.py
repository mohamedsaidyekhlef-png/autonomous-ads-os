from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.sqlite import SqliteSaver

from app.core.settings import get_settings


def _postgres_checkpoint_url(database_url: str) -> str:
    return database_url.replace(
        "postgresql+psycopg://",
        "postgresql://",
        1,
    )


def _sqlite_checkpoint_path(database_url: str) -> str:
    prefixes = (
        "sqlite+pysqlite:///",
        "sqlite:///",
    )

    database_path = ""

    for prefix in prefixes:
        if database_url.startswith(prefix):
            database_path = database_url.removeprefix(prefix)
            break

    if not database_path or database_path == ":memory:":
        return str(Path(".expert-review-checkpoints.sqlite3").resolve())

    source = Path(database_path).resolve()

    return str(source.with_name(f"{source.name}.langgraph-checkpoints.sqlite3"))


@contextmanager
def expert_review_checkpointer() -> Iterator[Any]:
    database_url = get_settings().database_url

    if database_url.startswith("postgresql"):
        connection_url = _postgres_checkpoint_url(database_url)

        with PostgresSaver.from_conn_string(connection_url) as saver:
            saver.setup()
            yield saver

        return

    checkpoint_path = _sqlite_checkpoint_path(database_url)

    with SqliteSaver.from_conn_string(checkpoint_path) as saver:
        yield saver
