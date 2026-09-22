"""Money arithmetic."""

from decimal import Decimal


class CurrencyMismatch(Exception):
    pass


class Money:
    def __init__(self, amount, currency: str) -> None:
        self.amount = Decimal(str(amount)).quantize(Decimal("0.01"))
        self.currency = currency

    def __add__(self, other: "Money") -> "Money":
        if other.currency != self.currency:
            raise CurrencyMismatch(f"{self.currency} + {other.currency}")
        return Money(self.amount + other.amount, self.currency)

    def __mul__(self, n: int) -> "Money":
        return Money(self.amount * n, self.currency)

    def __repr__(self) -> str:
        return f"Money({self.amount}, {self.currency!r})"
