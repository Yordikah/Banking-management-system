"""Text menu interface."""

from decimal import Decimal

from .errors import BankingError
from .services import accounts, transactions, users
from .validation import ACCOUNT_TYPES


# ---------------------------------------------------------------- helpers
def money(value) -> str:
    return f"{Decimal(str(value)):,.2f}"


def print_table(headers, rows) -> None:
    if not rows:
        print("  (no records)")
        return
    text_rows = [["" if v is None else str(v) for v in row] for row in rows]
    widths = [max(len(h), *(len(r[i]) for r in text_rows)) for i, h in enumerate(headers)]
    line = "+".join("-" * (w + 2) for w in widths)
    print("  " + " | ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print("  " + line)
    for r in text_rows:
        print("  " + " | ".join(v.ljust(w) for v, w in zip(r, widths)))


def ask(prompt: str) -> str:
    return input(f"  {prompt}: ").strip()


def confirm(prompt: str) -> bool:
    return ask(f"{prompt} (y/n)").lower() in ("y", "yes")


def pause() -> None:
    try:
        input("\n  Press Enter to continue...")
    except EOFError:
        pass


# ---------------------------------------------------------------- users
def add_user():
    print("\n-- Add user --")
    uid = users.add_user(
        ask("First name"), ask("Last name"), ask("Age"), ask("Occupation (optional)")
    )
    print(f"\n  User added with ID {uid}.")


def view_users():
    print("\n-- Users --")
    rows = users.list_users(ask("Search by name (leave blank for all)"))
    print_table(
        ["ID", "First name", "Last name", "Age", "Occupation", "Accounts", "Total balance"],
        [
            (r["user_id"], r["first_name"], r["last_name"], r["age"], r["occupation"],
             r["account_count"], money(r["total_balance"]))
            for r in rows
        ],
    )


def edit_user():
    print("\n-- Edit user --")
    current = users.get_user(ask("User ID"))
    print("  Leave a field blank to keep its current value.")
    first = ask(f"First name [{current['first_name']}]") or current["first_name"]
    last = ask(f"Last name [{current['last_name']}]") or current["last_name"]
    age = ask(f"Age [{current['age']}]") or current["age"]
    job = ask(f"Occupation [{current['occupation'] or ''}]") or current["occupation"]
    users.update_user(current["user_id"], first, last, age, job)
    print("\n  User updated.")


def delete_user():
    print("\n-- Delete user --")
    user = users.get_user(ask("User ID"))
    if confirm(f"Delete {user['first_name']} {user['last_name']}?"):
        users.delete_user(user["user_id"])
        print("\n  User deleted.")


# ---------------------------------------------------------------- accounts
def create_account():
    print("\n-- Create account --")
    user_id = ask("User ID")
    for i, kind in enumerate(ACCOUNT_TYPES, 1):
        print(f"    {i}) {kind}")
    kind = ask("Account type")
    opening = ask("Opening balance (blank = 0)")
    aid = accounts.create_account(user_id, kind, opening)
    print(f"\n  Account {aid} created.")


def view_accounts():
    print("\n-- Accounts --")
    rows = accounts.list_accounts(ask("User ID (leave blank for all)"))
    print_table(
        ["Account", "User", "Owner", "Type", "Balance", "Opened"],
        [
            (r["account_id"], r["user_id"], r["owner"], r["account_type"],
             money(r["balance"]), r["created_at"])
            for r in rows
        ],
    )


def close_account():
    print("\n-- Close account --")
    acc = accounts.get_account(ask("Account ID"))
    if confirm(f"Close {acc['account_type']} account {acc['account_id']} of {acc['owner']}?"):
        accounts.close_account(acc["account_id"])
        print("\n  Account closed.")


# ---------------------------------------------------------------- money
def deposit():
    print("\n-- Deposit --")
    balance = transactions.deposit(ask("Account ID"), ask("Amount"))
    print(f"\n  Deposit successful. New balance: {money(balance)}")


def withdraw():
    print("\n-- Withdraw --")
    balance = transactions.withdraw(ask("Account ID"), ask("Amount"))
    print(f"\n  Withdrawal successful. New balance: {money(balance)}")


def transfer():
    print("\n-- Transfer --")
    balance = transactions.transfer(ask("From account ID"), ask("To account ID"), ask("Amount"))
    print(f"\n  Transfer successful. Your new balance: {money(balance)}")


def check_balance():
    print("\n-- Balance --")
    acc = accounts.get_account(ask("Account ID"))
    print(f"\n  Account {acc['account_id']} ({acc['account_type']}, {acc['owner']}): "
          f"{money(acc['balance'])}")


def view_history():
    print("\n-- Transaction history --")
    rows = transactions.history(ask("Account ID (leave blank for all)"))
    print_table(
        ["ID", "Account", "Type", "Amount", "Date"],
        [
            (r["transaction_id"], r["account_id"], r["transaction_type"],
             money(r["amount"]), r["created_at"])
            for r in rows
        ],
    )


def summary():
    print("\n-- Bank summary --")
    s = accounts.bank_summary()
    print(f"  Users:          {s['users']}")
    print(f"  Accounts:       {s['accounts']}")
    print(f"  Total deposits: {money(s['deposits'])}")
    if s["by_type"]:
        print()
        print_table(
            ["Type", "Accounts", "Total"],
            [(r["account_type"], r["n"], money(r["total"])) for r in s["by_type"]],
        )


# ---------------------------------------------------------------- menu
MENU = [
    ("Users", [
        ("Add user", add_user),
        ("View / search users", view_users),
        ("Edit user", edit_user),
        ("Delete user", delete_user),
    ]),
    ("Accounts", [
        ("Create account", create_account),
        ("View accounts", view_accounts),
        ("Check balance", check_balance),
        ("Close account", close_account),
    ]),
    ("Transactions", [
        ("Deposit money", deposit),
        ("Withdraw money", withdraw),
        ("Transfer money", transfer),
        ("Transaction history", view_history),
    ]),
    ("Reports", [
        ("Bank summary", summary),
    ]),
]


def main_menu() -> None:
    actions = {}
    while True:
        print("\n" + "=" * 44)
        print("        BANKING MANAGEMENT SYSTEM")
        print("=" * 44)
        n = 1
        for section, items in MENU:
            print(f"\n {section}")
            for label, func in items:
                print(f"   {n:>2}. {label}")
                actions[str(n)] = func
                n += 1
        print("\n    0. Exit")

        choice = input("\nEnter your choice: ").strip()
        if choice == "0":
            print("Goodbye!")
            return
        action = actions.get(choice)
        if action is None:
            print("Invalid choice. Please try again.")
            continue
        try:
            action()
        except BankingError as err:
            print(f"\n  Error: {err}")
        except (KeyboardInterrupt, EOFError):
            print("\n  Cancelled.")
        pause()
