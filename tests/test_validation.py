"""Unit tests for input validation. No database needed:  python -m unittest"""

import unittest
from decimal import Decimal

from banking.errors import ValidationError
from banking.validation import (
    parse_account_type,
    parse_age,
    parse_amount,
    parse_id,
    parse_opening_balance,
    require_text,
)


class TextTests(unittest.TestCase):
    def test_trims(self):
        self.assertEqual(require_text("  Ali ", "Name"), "Ali")

    def test_blank_rejected(self):
        with self.assertRaises(ValidationError):
            require_text("   ", "Name")

    def test_too_long_rejected(self):
        with self.assertRaises(ValidationError):
            require_text("x" * 51, "Name")


class NumberTests(unittest.TestCase):
    def test_ids(self):
        self.assertEqual(parse_id(" 7 "), 7)
        for bad in ("0", "-3", "abc", "", None, "1.5"):
            with self.assertRaises(ValidationError):
                parse_id(bad)

    def test_age(self):
        self.assertEqual(parse_age("30"), 30)
        for bad in ("17", "121", "thirty"):
            with self.assertRaises(ValidationError):
                parse_age(bad)


class MoneyTests(unittest.TestCase):
    def test_amount_valid(self):
        self.assertEqual(parse_amount("100"), Decimal("100.00"))
        self.assertEqual(parse_amount("1,250.5"), Decimal("1250.50"))

    def test_amount_rejects_zero_negative_and_junk(self):
        for bad in ("0", "-5", "abc", "", "NaN", "Infinity", "10.999"):
            with self.assertRaises(ValidationError, msg=bad):
                parse_amount(bad)

    def test_amount_rejects_huge(self):
        with self.assertRaises(ValidationError):
            parse_amount("7500000000000")

    def test_opening_balance(self):
        self.assertEqual(parse_opening_balance(""), Decimal("0.00"))
        self.assertEqual(parse_opening_balance("0"), Decimal("0.00"))
        self.assertEqual(parse_opening_balance("50.25"), Decimal("50.25"))
        with self.assertRaises(ValidationError):
            parse_opening_balance("-1")


class AccountTypeTests(unittest.TestCase):
    def test_by_name_and_number(self):
        self.assertEqual(parse_account_type("Savings"), "savings")
        self.assertEqual(parse_account_type("2"), "checking")
        self.assertEqual(parse_account_type("3"), "business")

    def test_invalid(self):
        for bad in ("", "gold", "4", "0"):
            with self.assertRaises(ValidationError):
                parse_account_type(bad)


if __name__ == "__main__":
    unittest.main()
