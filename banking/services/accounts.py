"""Bank account operations."""

from decimal import Decimal

from ..database import db_cursor
from ..errors import BankingError, NotFoundError
from ..validation import parse_account_type, parse_id, parse_opening_balance


def create_account(user_id, account_type, opening_balance="0") -> int:
    """Open an account for an existing user and return the new account_id.

    A non-zero opening balance is also recorded as a 'credit' transaction so
    the transaction history always adds up to the balance.
    """
    uid = parse_id(user_id, "User ID")
    kind = parse_account_type(account_type)
    balance = parse_opening_balance(opening_balance)

    with db_cursor() as cur:
        cur.execute("SELECT 1 FROM users WHERE user_id = %s", (uid,))
        if cur.fetchone() is None:
            raise NotFoundError(f"User {uid} does not exist. Add the user first.")

        cur.execute(
            "INSERT INTO accounts (user_id, account_type, balance) VALUES (%s, %s, %s)",
            (uid, kind, balance),
        )
        account_id = cur.lastrowid

        if balance > 0:
            cur.execute(
                "INSERT INTO transactions (account_id, transaction_type, amount) "
                "VALUES (%s, 'credit', %s)",
                (account_id, balance),
            )
        return account_id


def list_accounts(user_id=None) -> list:
    """All accounts (or one user's) with the owner's name."""
    query = (
        "SELECT a.account_id, a.user_id, "
        "       CONCAT(u.first_name, ' ', u.last_name) AS owner, "
        "       a.account_type, a.balance, a.created_at "
        "FROM accounts a JOIN users u ON u.user_id = a.user_id "
    )
    params = ()
    if user_id not in (None, ""):
        query += "WHERE a.user_id = %s "
        params = (parse_id(user_id, "User ID"),)
    query += "ORDER BY a.account_id"

    with db_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()


def get_account(account_id) -> dict:
    aid = parse_id(account_id, "Account ID")
    with db_cursor() as cur:
        cur.execute(
            "SELECT a.*, CONCAT(u.first_name, ' ', u.last_name) AS owner "
            "FROM accounts a JOIN users u ON u.user_id = a.user_id "
            "WHERE a.account_id = %s",
            (aid,),
        )
        row = cur.fetchone()
    if row is None:
        raise NotFoundError(f"Account {aid} does not exist.")
    return row


def close_account(account_id) -> None:
    """Close (delete) an account. Its balance must be zero."""
    aid = parse_id(account_id, "Account ID")
    with db_cursor() as cur:
        cur.execute("SELECT balance FROM accounts WHERE account_id = %s FOR UPDATE", (aid,))
        row = cur.fetchone()
        if row is None:
            raise NotFoundError(f"Account {aid} does not exist.")
        if Decimal(str(row["balance"])) != 0:
            raise BankingError(
                f"Account {aid} still holds {Decimal(str(row['balance'])):.2f}. "
                "Withdraw or transfer it before closing."
            )
        cur.execute("DELETE FROM transactions WHERE account_id = %s", (aid,))
        cur.execute("DELETE FROM accounts WHERE account_id = %s", (aid,))


def bank_summary() -> dict:
    """Totals for the dashboard / report screen."""
    with db_cursor() as cur:
        cur.execute("SELECT COUNT(*) AS users FROM users")
        users = cur.fetchone()["users"]
        cur.execute(
            "SELECT COUNT(*) AS accounts, COALESCE(SUM(balance), 0) AS deposits FROM accounts"
        )
        acc = cur.fetchone()
        cur.execute(
            "SELECT account_type, COUNT(*) AS n, COALESCE(SUM(balance), 0) AS total "
            "FROM accounts GROUP BY account_type ORDER BY account_type"
        )
        by_type = cur.fetchall()
    return {
        "users": users,
        "accounts": acc["accounts"],
        "deposits": acc["deposits"],
        "by_type": by_type,
    }
