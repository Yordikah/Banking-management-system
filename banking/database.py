"""MySQL connection handling."""

from contextlib import contextmanager

from .config import DB_CONFIG
from .errors import DatabaseError


def get_connection():
    """Open a new MySQL connection, raising DatabaseError on failure."""
    try:
        import mysql.connector
    except ImportError as exc:  # pragma: no cover - depends on environment
        raise DatabaseError(
            "mysql-connector-python is not installed. Run: pip install -r requirements.txt"
        ) from exc

    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        raise DatabaseError(f"Could not connect to MySQL: {err}") from err


@contextmanager
def db_cursor():
    """Yield a dictionary cursor inside one transaction.

    Commits when the block finishes, rolls back on any exception, and always
    closes the connection. Every multi-step operation (e.g. a transfer) runs
    inside a single `with db_cursor()` block so it is all-or-nothing.
    """
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        yield cursor
        conn.commit()
    except Exception as exc:
        conn.rollback()
        _reraise_mysql_error(exc)
        raise
    finally:
        cursor.close()
        conn.close()


def _reraise_mysql_error(exc: Exception) -> None:
    """Turn raw driver errors into DatabaseError so callers handle one type."""
    try:
        import mysql.connector
    except ImportError:  # pragma: no cover
        return
    if isinstance(exc, mysql.connector.Error):
        raise DatabaseError(f"Database error: {exc}") from exc
