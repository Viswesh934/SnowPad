"""DuckDB connection and session management for SnowPad."""

from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional, Union
import duckdb

from snowpad.config import settings
from snowpad.db.schema import SCHEMA_DDL


def get_db_path(db_path: Optional[Union[Path, str]] = None) -> str:
    """Return the absolute path string for the DuckDB file."""
    target = Path(db_path) if db_path else settings.db_path
    target.parent.mkdir(parents=True, exist_ok=True)
    return str(target)


@contextmanager
def get_connection(db_path: Optional[Union[Path, str]] = None) -> Generator[duckdb.DuckDBPyConnection, None, None]:
    """Provide a thread-safe DuckDB connection context."""
    path_str = get_db_path(db_path)
    conn = duckdb.connect(database=path_str, read_only=False)
    try:
        yield conn
    finally:
        conn.close()


def init_db(db_path: Optional[Union[Path, str]] = None) -> None:
    """Initialize DuckDB tables and analytical views."""
    with get_connection(db_path) as conn:
        conn.execute(SCHEMA_DDL)
