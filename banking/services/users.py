"""User (customer) operations."""

from ..database import db_cursor
from ..errors import BankingError, NotFoundError
from ..validation import optional_text, parse_age, parse_id, require_text


def add_user(first_name, last_name, age, occupation=None) -> int:
    """Create a user and return the new user_id."""
    first = require_text(first_name, "First name")
    last = require_text(last_name, "Last name")
    age_value = parse_age(age)
    job = optional_text(occupation, "Occupation")

    with db_cursor() as cur:
        cur.execute(
            "INSERT INTO users (first_name, last_name, age, occupation) "
            "VALUES (%s, %s, %s, %s)",
            (first, last, age_value, job),
        )
        return cur.lastrowid


def list_users(search: str = "") -> list:
    """All users with how many accounts they hold and their total balance."""
    query = (
        "SELECT u.user_id, u.first_name, u.last_name, u.age, u.occupation, "
        "       COUNT(a.account_id) AS account_count, "
        "       COALESCE(SUM(a.balance), 0) AS total_balance "
        "FROM users u LEFT JOIN accounts a ON a.user_id = u.user_id "
    )
    params = ()
    term = (search or "").strip()
    if term:
        query += "WHERE u.first_name LIKE %s OR u.last_name LIKE %s "
        params = (f"%{term}%", f"%{term}%")
    query += "GROUP BY u.user_id ORDER BY u.user_id"

    with db_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def get_user(user_id) -> dict:
    uid = parse_id(user_id, "User ID")
    with db_cursor() as cur:
        cur.execute("SELECT * FROM users WHERE user_id = %s", (uid,))
        row = cur.fetchone()
    if row is None:
        raise NotFoundError(f"User {uid} does not exist.")
    return row


def update_user(user_id, first_name, last_name, age, occupation=None) -> None:
    uid = parse_id(user_id, "User ID")
    first = require_text(first_name, "First name")
    last = require_text(last_name, "Last name")
    age_value = parse_age(age)
    job = optional_text(occupation, "Occupation")

    with db_cursor() as cur:
        cur.execute(
            "UPDATE users SET first_name = %s, last_name = %s, age = %s, occupation = %s "
            "WHERE user_id = %s",
            (first, last, age_value, job, uid),
        )
        if cur.rowcount == 0:
            cur.execute("SELECT 1 FROM users WHERE user_id = %s", (uid,))
            if cur.fetchone() is None:
                raise NotFoundError(f"User {uid} does not exist.")


def delete_user(user_id) -> None:
    """Delete a user. Refused while the user still has accounts."""
    uid = parse_id(user_id, "User ID")
    with db_cursor() as cur:
        cur.execute("SELECT 1 FROM users WHERE user_id = %s", (uid,))
        if cur.fetchone() is None:
            raise NotFoundError(f"User {uid} does not exist.")
        cur.execute("SELECT COUNT(*) AS n FROM accounts WHERE user_id = %s", (uid,))
        if cur.fetchone()["n"] > 0:
            raise BankingError(f"User {uid} still has accounts. Close them first.")
        cur.execute("DELETE FROM users WHERE user_id = %s", (uid,))
