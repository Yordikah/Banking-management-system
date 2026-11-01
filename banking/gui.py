"""Tkinter desktop interface with Users, Accounts, Transactions and Summary tabs."""

import tkinter as tk
from decimal import Decimal
from tkinter import messagebox, ttk

from .errors import BankingError
from .services import accounts, transactions, users
from .validation import ACCOUNT_TYPES


def money(value) -> str:
    return f"{Decimal(str(value)):,.2f}"


def make_table(parent, columns, widths):
    frame = ttk.Frame(parent)
    tree = ttk.Treeview(frame, columns=[c for c, _ in columns], show="headings", height=12)
    for (key, title), width in zip(columns, widths):
        tree.heading(key, text=title)
        anchor = "e" if key in ("balance", "amount", "total_balance") else "w"
        tree.column(key, width=width, anchor=anchor)
    scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    return tree


def fill_table(tree, rows):
    tree.delete(*tree.get_children())
    for row in rows:
        tree.insert("", "end", values=row)


def selected_id(tree):
    sel = tree.selection()
    return tree.item(sel[0], "values")[0] if sel else None


def labeled_entry(parent, label, row, col=0, width=22):
    ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", padx=5, pady=4)
    entry = ttk.Entry(parent, width=width)
    entry.grid(row=row, column=col + 1, sticky="w", padx=5, pady=4)
    return entry


class BankingApp:
    def __init__(self, root):
        self.root = root
        root.title("Banking Management System")
        root.geometry("980x640")
        root.minsize(820, 540)

        ttk.Style().configure("Title.TLabel", font=("Segoe UI", 18, "bold"))
        ttk.Label(root, text="Banking Management System", style="Title.TLabel").pack(pady=(12, 6))

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.users_tab = ttk.Frame(self.notebook)
        self.accounts_tab = ttk.Frame(self.notebook)
        self.tx_tab = ttk.Frame(self.notebook)
        self.summary_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.users_tab, text="  Users  ")
        self.notebook.add(self.accounts_tab, text="  Accounts  ")
        self.notebook.add(self.tx_tab, text="  Transactions  ")
        self.notebook.add(self.summary_tab, text="  Summary  ")

        self.status = tk.StringVar(value="Ready")
        ttk.Label(root, textvariable=self.status, relief="sunken", anchor="w").pack(
            fill="x", side="bottom"
        )

        self._build_users()
        self._build_accounts()
        self._build_transactions()
        self._build_summary()
        self.notebook.bind("<<NotebookTabChanged>>", lambda _e: self.refresh_all())
        self.refresh_all()

    # ------------------------------------------------------------ plumbing
    def run(self, action, success=None):
        """Run a service call, show friendly errors, refresh the views."""
        try:
            result = action()
        except BankingError as err:
            messagebox.showerror("Error", str(err))
            self.status.set(f"Error: {err}")
            return None
        if success:
            msg = success(result) if callable(success) else success
            self.status.set(msg)
            messagebox.showinfo("Success", msg)
        self.refresh_all()
        return result

    def refresh_all(self):
        try:
            self._refresh_users()
            self._refresh_accounts()
            self._refresh_transactions()
            self._refresh_summary()
        except BankingError as err:
            self.status.set(f"Error: {err}")

    # ------------------------------------------------------------ users tab
    def _build_users(self):
        form = ttk.LabelFrame(self.users_tab, text="User details")
        form.pack(fill="x", padx=10, pady=10)
        self.u_first = labeled_entry(form, "First name", 0, 0)
        self.u_last = labeled_entry(form, "Last name", 0, 2)
        self.u_age = labeled_entry(form, "Age", 1, 0)
        self.u_job = labeled_entry(form, "Occupation", 1, 2)

        buttons = ttk.Frame(form)
        buttons.grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=6)
        ttk.Button(buttons, text="Add user", command=self.add_user).pack(side="left", padx=3)
        ttk.Button(buttons, text="Update selected", command=self.update_user).pack(side="left", padx=3)
        ttk.Button(buttons, text="Delete selected", command=self.delete_user).pack(side="left", padx=3)
        ttk.Button(buttons, text="Clear", command=self.clear_user_form).pack(side="left", padx=3)

        search = ttk.Frame(self.users_tab)
        search.pack(fill="x", padx=10)
        ttk.Label(search, text="Search:").pack(side="left")
        self.u_search = ttk.Entry(search, width=30)
        self.u_search.pack(side="left", padx=5)
        self.u_search.bind("<KeyRelease>", lambda _e: self._refresh_users())

        self.users_table = make_table(
            self.users_tab,
            [("id", "ID"), ("first", "First name"), ("last", "Last name"), ("age", "Age"),
             ("job", "Occupation"), ("n", "Accounts"), ("total_balance", "Total balance")],
            [50, 140, 140, 60, 170, 80, 130],
        )
        self.users_table.bind("<<TreeviewSelect>>", self._on_user_select)

    def _refresh_users(self):
        rows = users.list_users(self.u_search.get())
        fill_table(self.users_table, [
            (r["user_id"], r["first_name"], r["last_name"], r["age"], r["occupation"] or "",
             r["account_count"], money(r["total_balance"]))
            for r in rows
        ])

    def _on_user_select(self, _event):
        values = self.users_table.item(self.users_table.selection()[0], "values") \
            if self.users_table.selection() else None
        if not values:
            return
        for entry, value in zip((self.u_first, self.u_last, self.u_age, self.u_job), values[1:5]):
            entry.delete(0, tk.END)
            entry.insert(0, value)

    def clear_user_form(self):
        for entry in (self.u_first, self.u_last, self.u_age, self.u_job):
            entry.delete(0, tk.END)
        self.users_table.selection_remove(self.users_table.selection())

    def add_user(self):
        uid = self.run(
            lambda: users.add_user(self.u_first.get(), self.u_last.get(),
                                   self.u_age.get(), self.u_job.get()),
            lambda new_id: f"User added with ID {new_id}.",
        )
        if uid:
            self.clear_user_form()

    def update_user(self):
        uid = selected_id(self.users_table)
        if not uid:
            messagebox.showwarning("Update user", "Select a user in the table first.")
            return
        self.run(
            lambda: users.update_user(uid, self.u_first.get(), self.u_last.get(),
                                      self.u_age.get(), self.u_job.get()),
            f"User {uid} updated.",
        )

    def delete_user(self):
        uid = selected_id(self.users_table)
        if not uid:
            messagebox.showwarning("Delete user", "Select a user in the table first.")
            return
        if messagebox.askyesno("Delete user", f"Delete user {uid}?"):
            self.run(lambda: users.delete_user(uid), f"User {uid} deleted.")
            self.clear_user_form()

    # ------------------------------------------------------------ accounts tab
    def _build_accounts(self):
        form = ttk.LabelFrame(self.accounts_tab, text="Open a new account")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Owner").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.a_owner = ttk.Combobox(form, width=30, state="readonly")
        self.a_owner.grid(row=0, column=1, sticky="w", padx=5, pady=4)

        ttk.Label(form, text="Type").grid(row=0, column=2, sticky="w", padx=5, pady=4)
        self.a_type = ttk.Combobox(form, values=ACCOUNT_TYPES, width=14, state="readonly")
        self.a_type.current(0)
        self.a_type.grid(row=0, column=3, sticky="w", padx=5, pady=4)

        self.a_opening = labeled_entry(form, "Opening balance", 1, 0)
        self.a_opening.insert(0, "0")

        buttons = ttk.Frame(form)
        buttons.grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=6)
        ttk.Button(buttons, text="Create account", command=self.create_account).pack(side="left", padx=3)
        ttk.Button(buttons, text="Close selected account", command=self.close_account).pack(side="left", padx=3)

        self.accounts_table = make_table(
            self.accounts_tab,
            [("id", "Account"), ("uid", "User"), ("owner", "Owner"), ("type", "Type"),
             ("balance", "Balance"), ("opened", "Opened")],
            [70, 60, 200, 110, 130, 170],
        )

    def _refresh_accounts(self):
        all_users = users.list_users()
        self._owner_ids = [u["user_id"] for u in all_users]
        self.a_owner["values"] = [
            f"{u['user_id']} - {u['first_name']} {u['last_name']}" for u in all_users
        ]
        rows = accounts.list_accounts()
        fill_table(self.accounts_table, [
            (r["account_id"], r["user_id"], r["owner"], r["account_type"],
             money(r["balance"]), r["created_at"])
            for r in rows
        ])
        self._account_choices = [
            f"{r['account_id']} - {r['owner']} ({r['account_type']})" for r in rows
        ]

    def create_account(self):
        idx = self.a_owner.current()
        if idx < 0:
            messagebox.showwarning("Create account", "Choose the account owner first.")
            return
        user_id = self._owner_ids[idx]
        self.run(
            lambda: accounts.create_account(user_id, self.a_type.get(), self.a_opening.get()),
            lambda aid: f"Account {aid} created.",
        )

    def close_account(self):
        aid = selected_id(self.accounts_table)
        if not aid:
            messagebox.showwarning("Close account", "Select an account in the table first.")
            return
        if messagebox.askyesno("Close account", f"Close account {aid}? Its history is removed."):
            self.run(lambda: accounts.close_account(aid), f"Account {aid} closed.")

    # ------------------------------------------------------------ transactions tab
    def _build_transactions(self):
        form = ttk.LabelFrame(self.tx_tab, text="Move money")
        form.pack(fill="x", padx=10, pady=10)

        ttk.Label(form, text="Account").grid(row=0, column=0, sticky="w", padx=5, pady=4)
        self.t_account = ttk.Combobox(form, width=36)
        self.t_account.grid(row=0, column=1, sticky="w", padx=5, pady=4)
        self.t_account.bind("<<ComboboxSelected>>", lambda _e: self._refresh_transactions())

        ttk.Label(form, text="Transfer to").grid(row=1, column=0, sticky="w", padx=5, pady=4)
        self.t_target = ttk.Combobox(form, width=36)
        self.t_target.grid(row=1, column=1, sticky="w", padx=5, pady=4)

        self.t_amount = labeled_entry(form, "Amount", 0, 2, width=14)

        buttons = ttk.Frame(form)
        buttons.grid(row=2, column=0, columnspan=4, sticky="w", padx=5, pady=6)
        ttk.Button(buttons, text="Deposit", command=self.deposit).pack(side="left", padx=3)
        ttk.Button(buttons, text="Withdraw", command=self.withdraw).pack(side="left", padx=3)
        ttk.Button(buttons, text="Transfer", command=self.transfer).pack(side="left", padx=3)
        ttk.Button(buttons, text="Show all history",
                   command=self.show_all_history).pack(side="left", padx=12)

        self.t_balance = tk.StringVar(value="")
        ttk.Label(self.tx_tab, textvariable=self.t_balance,
                  font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12)

        self.tx_table = make_table(
            self.tx_tab,
            [("id", "ID"), ("acc", "Account"), ("type", "Type"), ("amount", "Amount"),
             ("date", "Date")],
            [60, 80, 90, 130, 180],
        )

    @staticmethod
    def _id_from_choice(text):
        return text.split(" - ", 1)[0].strip() if text else ""

    def _refresh_transactions(self):
        choices = getattr(self, "_account_choices", [])
        self.t_account["values"] = choices
        self.t_target["values"] = choices
        aid = self._id_from_choice(self.t_account.get())
        try:
            rows = transactions.history(aid or None)
            self.t_balance.set(
                f"Balance of account {aid}: {money(transactions.get_balance(aid))}" if aid
                else "All accounts (latest 100 transactions)"
            )
        except BankingError as err:
            rows = []
            self.t_balance.set(str(err))
        fill_table(self.tx_table, [
            (r["transaction_id"], r["account_id"], r["transaction_type"],
             money(r["amount"]), r["created_at"])
            for r in rows
        ])

    def show_all_history(self):
        self.t_account.set("")
        self._refresh_transactions()

    def _money_action(self, func, verb):
        aid = self._id_from_choice(self.t_account.get())
        result = self.run(
            lambda: func(aid, self.t_amount.get()),
            lambda bal: f"{verb} successful. New balance: {money(bal)}",
        )
        if result is not None:
            self.t_amount.delete(0, tk.END)

    def deposit(self):
        self._money_action(transactions.deposit, "Deposit")

    def withdraw(self):
        self._money_action(transactions.withdraw, "Withdrawal")

    def transfer(self):
        src = self._id_from_choice(self.t_account.get())
        dst = self._id_from_choice(self.t_target.get())
        result = self.run(
            lambda: transactions.transfer(src, dst, self.t_amount.get()),
            lambda bal: f"Transfer successful. New balance of account {src}: {money(bal)}",
        )
        if result is not None:
            self.t_amount.delete(0, tk.END)

    # ------------------------------------------------------------ summary tab
    def _build_summary(self):
        box = ttk.Frame(self.summary_tab)
        box.pack(fill="x", padx=20, pady=20)
        self.s_users = tk.StringVar()
        self.s_accounts = tk.StringVar()
        self.s_deposits = tk.StringVar()
        for col, (title, var) in enumerate(
            (("Users", self.s_users), ("Accounts", self.s_accounts),
             ("Total deposits", self.s_deposits))
        ):
            card = ttk.LabelFrame(box, text=title)
            card.grid(row=0, column=col, padx=10, sticky="nsew")
            ttk.Label(card, textvariable=var, font=("Segoe UI", 20, "bold")).pack(padx=30, pady=15)
            box.columnconfigure(col, weight=1)

        ttk.Label(self.summary_tab, text="By account type").pack(anchor="w", padx=12)
        self.summary_table = make_table(
            self.summary_tab,
            [("type", "Type"), ("n", "Accounts"), ("total_balance", "Total balance")],
            [160, 100, 160],
        )

    def _refresh_summary(self):
        s = accounts.bank_summary()
        self.s_users.set(str(s["users"]))
        self.s_accounts.set(str(s["accounts"]))
        self.s_deposits.set(money(s["deposits"]))
        fill_table(self.summary_table, [
            (r["account_type"], r["n"], money(r["total"])) for r in s["by_type"]
        ])


def launch() -> None:
    root = tk.Tk()
    BankingApp(root)
    root.mainloop()
