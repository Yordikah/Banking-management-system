"""Deposits, withdrawals, transfers and transaction history.

Every money movement locks the affected account rows with SELECT ... FOR UPDATE
and runs in one database transaction, so two simultaneous withdrawals can never
overdraw an account and a transfer can never half-complete.
"""

from decimal import Decimal

from ..database import db_cursor
from ..errors import InsufficientFundsError, NotFoundError, ValidationError
from ..validation import parse_amount, parse_id


def _lock_balance(cur, account_id: int) -> Decimal:
    cur.execute("SELECT balance FROM accounts WHERE account_id = %s FOR UPDATE", (account_id,))
    row = cur.fetchone()
    if row is None:
        raise NotFoundError(f"Account {account_id} does not exist.")
    return Decimal(str(row["balance"]))


def _apply(cur, account_id: int, kind: str, amount: Decimal) -> None:
    sign = "+" if kind == "credit" else "-"
    cur.execute(
        f"UPDATE accounts SET balance = balance {sign} %s WHERE account_id = %s",
        (amount, account_id),
    )
    cur.execute(
        "INSERT INTO transactions (account_id, transaction_type, amount) VALUES (%s, %s, %s)",
        (account_id, kind, amount),
    )


def deposit(account_id, amount) -> Decimal:
    """Add money to an account. Returns the new balance."""
    aid = parse_id(account_id, "Account ID")
    value = parse_amount(amount, "Deposit amount")
    with db_cursor() as cur:
        balance = _lock_balance(cur, aid)
        _apply(cur, aid, "credit", value)
        return balance + value


def withdraw(account_id, amount) -> Decimal:
    """Take money out of an account. Returns the new balance."""
    aid = parse_id(account_id, "Account ID")
    value = parse_amount(amount, "Withdrawal amount")
    with db_cursor() as cur:
        balance = _lock_balance(cur, aid)
        if value > balance:
            raise InsufficientFundsError(
                f"Insufficient funds: account {aid} has {balance:.2f}, tried to withdraw {value:.2f}."
            )
        _apply(cur, aid, "debit", value)
        return balance - value


def transfer(from_account_id, to_account_id, amount) -> Decimal:
    """Move money between two accounts. Returns the sender's new balance."""
    src = parse_id(from_account_id, "From account ID")
    dst = parse_id(to_account_id, "To account ID")
    value = parse_amount(amount, "Transfer amount")
    if src == dst:
        raise ValidationError("Cannot transfer to the same account.")

    with db_cursor() as cur:
        # Lock both rows in a fixed order to avoid deadlocks.
        balances = {aid: _lock_balance(cur, aid) for aid in sorted((src, dst))}
        if value > balances[src]:
            raise InsufficientFundsError(
                f"Insufficient funds: account {src} has {balances[src]:.2f}, "
                f"tried to transfer {value:.2f}."
            )
        _apply(cur, src, "debit", value)
        _apply(cur, dst, "credit", value)
        return balances[src] - value


def get_balance(account_id) -> Decimal:
    aid = parse_id(account_id, "Account ID")
    with db_cursor() as cur:
        cur.execute("SELECT balance FROM accounts WHERE account_id = %s", (aid,))
        row = cur.fetchone()
    if row is None:
        raise NotFoundError(f"Account {aid} does not exist.")
    return Decimal(str(row["balance"]))


def history(account_id=None, limit: int = 100) -> list:
    """Most recent transactions, for one account or for the whole bank."""
    query = (
        "SELECT transaction_id, account_id, transaction_type, amount, created_at "
        "FROM transactions "
    )
    params: tuple = ()
    if account_id not in (None, ""):
        aid = parse_id(account_id, "Account ID")
        with db_cursor() as cur:
            cur.execute("SELECT 1 FROM accounts WHERE account_id = %s", (aid,))
            if cur.fetchone() is None:
                raise NotFoundError(f"Account {aid} does not exist.")
        query += "WHERE account_id = %s "
        params = (aid,)
    query += "ORDER BY created_at DESC, transaction_id DESC LIMIT %s"
    params += (int(limit),)

    with db_cursor() as cur:
        cur.execute(query, params)
        return cur.fetchall()
