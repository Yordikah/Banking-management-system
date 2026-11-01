"""Input parsing and validation. Pure functions, no database access."""

from decimal import Decimal, InvalidOperation

from .errors import ValidationError

ACCOUNT_TYPES = ("savings", "checking", "business")
MAX_AMOUNT = Decimal("1000000000")  # fits DECIMAL(15, 2)


def require_text(value, field: str, max_len: int = 50) -> str:
    text = (value or "").strip()
    if not text:
        raise ValidationError(f"{field} is required.")
    if len(text) > max_len:
        raise ValidationError(f"{field} must be at most {max_len} characters.")
    return text


def optional_text(value, field: str, max_len: int = 100):
    text = (value or "").strip()
    if not text:
        return None
    if len(text) > max_len:
        raise ValidationError(f"{field} must be at most {max_len} characters.")
    return text


def parse_id(value, field: str = "ID") -> int:
    try:
        number = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValidationError(f"{field} must be a whole number.") from None
    if number <= 0:
        raise ValidationError(f"{field} must be positive.")
    return number


def parse_age(value) -> int:
    try:
        age = int(str(value).strip())
    except (TypeError, ValueError):
        raise ValidationError("Age must be a whole number.") from None
    if not 18 <= age <= 120:
        raise ValidationError("Age must be between 18 and 120.")
    return age


def _parse_money(value, field: str) -> Decimal:
    try:
        amount = Decimal(str(value).strip().replace(",", ""))
    except (InvalidOperation, TypeError):
        raise ValidationError(f"{field} must be a number, e.g. 250 or 99.95.") from None
    if not amount.is_finite():
        raise ValidationError(f"{field} must be a number.")
    if amount.as_tuple().exponent < -2:
        raise ValidationError(f"{field} can have at most 2 decimal places.")
    if amount >= MAX_AMOUNT:
        raise ValidationError(f"{field} is too large.")
    return amount.quantize(Decimal("0.01"))


def parse_amount(value, field: str = "Amount") -> Decimal:
    """A transaction amount: strictly greater than zero."""
    amount = _parse_money(value, field)
    if amount <= 0:
        raise ValidationError(f"{field} must be greater than zero.")
    return amount


def parse_opening_balance(value) -> Decimal:
    """An opening balance: zero or more. Blank means zero."""
    if value is None or str(value).strip() == "":
        return Decimal("0.00")
    amount = _parse_money(value, "Opening balance")
    if amount < 0:
        raise ValidationError("Opening balance cannot be negative.")
    return amount


def parse_account_type(value) -> str:
    """Accept a name ('savings') or its menu number ('1')."""
    text = (value or "").strip().lower()
    if text.isdigit() and 1 <= int(text) <= len(ACCOUNT_TYPES):
        return ACCOUNT_TYPES[int(text) - 1]
    if text in ACCOUNT_TYPES:
        return text
    options = ", ".join(f"{i}) {t}" for i, t in enumerate(ACCOUNT_TYPES, 1))
    raise ValidationError(f"Account type must be one of: {options}.")
