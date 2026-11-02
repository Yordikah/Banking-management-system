# Banking Management System

A banking management system written in **Python** with a **MySQL** database, built for
COMP 337 – Database Management Systems, Lab Manual 1 (European University of Lefke).

The full lab report is in [`docs/Lab_Report.pdf`](docs/Lab_Report.pdf).

It has two interfaces over the same business logic:

- a **text menu** (`python main.py`)
- a **Tkinter desktop app** (`python main.py --gui`)

## Features

| Area | What you can do |
|---|---|
| Users | Add, view, search by name, edit, delete (blocked while the user still has accounts) |
| Accounts | Open savings / checking / business accounts, view all or per user, check balance, close (only at zero balance) |
| Transactions | Deposit, withdraw, transfer between accounts, full transaction history |
| Reports | Bank summary: number of users and accounts, total deposits, totals per account type |

### How correctness is protected

- **Atomic operations** – every deposit, withdrawal and transfer runs in one database
  transaction; if any step fails, everything is rolled back.
- **No overdrafts, even with simultaneous users** – balances are read with
  `SELECT … FOR UPDATE`, so two withdrawals can't both pass the balance check.
  Transfers lock both accounts in a fixed order to avoid deadlocks.
- **Exact money** – amounts are `DECIMAL(15,2)` in MySQL and `Decimal` in Python, never
  floats, and are validated (positive, max 2 decimals, not absurdly large).
- **SQL injection safe** – all queries use parameters (`%s`), never string formatting of
  user input.
- **Database constraints** – foreign keys plus `CHECK` constraints for age, balance ≥ 0,
  account type and transaction type.
- **Audit trail** – an opening balance is logged as a credit, so an account's history always
  adds up to its balance.
- **No secrets in code** – credentials come from a `.env` file that is git-ignored.

## Project structure

```
banking-management-system/
├── main.py                   # entry point (CLI by default, --gui for the window)
├── banking/
│   ├── config.py             # reads DB settings from .env / environment
│   ├── database.py           # connection + transactional cursor
│   ├── errors.py             # friendly exception types
│   ├── validation.py         # input parsing/validation (pure functions)
│   ├── services/
│   │   ├── users.py
│   │   ├── accounts.py
│   │   └── transactions.py
│   ├── cli.py                # text menu
│   └── gui.py                # Tkinter interface
├── sql/
│   ├── schema.sql            # creates database + tables
│   └── seed.sql              # optional sample data
├── tests/
│   └── test_validation.py
├── requirements.txt
└── .env.example
```

## Database design

```
users (user_id PK, first_name, last_name, age, occupation)
   │ 1
   │
   │ N
accounts (account_id PK, user_id FK, account_type, balance, created_at)
   │ 1
   │
   │ N
transactions (transaction_id PK, account_id FK, transaction_type, amount, created_at)
```

`transaction_type` is `credit` (money in) or `debit` (money out). A transfer is recorded as a
debit on the sender and a credit on the receiver.

## Setup

**Requirements:** Python 3.9+ and MySQL 8 (or MariaDB 10.4+).

1. Clone and install the driver:
   ```bash
   git clone https://github.com/Yordikah/banking-management-system.git
   cd banking-management-system
   pip install -r requirements.txt
   ```
2. Create the database (in a terminal, or open `sql/schema.sql` in MySQL Workbench and run it):
   ```bash
   mysql -u root -p < sql/schema.sql
   mysql -u root -p banking_app < sql/seed.sql     # optional sample data
   ```
3. Configure the connection:
   ```bash
   cp .env.example .env        # Windows: copy .env.example .env
   ```
   then put your MySQL password in `.env`.
4. Run:
   ```bash
   python main.py           # text menu
   python main.py --gui     # desktop window
   ```

### Using an existing `banking_app` database

If you already created `users`, `accounts` and `transactions` tables with the same column
names, the app works with them as-is; `schema.sql` uses `CREATE TABLE IF NOT EXISTS` and
won't touch existing tables. Note the app expects `transaction_type` values `credit` and
`debit` and account types `savings`, `checking` or `business`.

## Tests

```bash
python -m unittest -v
```

The tests cover all input validation and need no database.

## Author

Yordanos Mezgebe Kahsay (2503060413) — submitted to Mr. Salman Khan.
