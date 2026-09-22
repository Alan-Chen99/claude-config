"""Invoice assembly."""

from .money import Money


class Line:
    def __init__(self, sku: str, qty: int, unit: Money) -> None:
        self.sku = sku
        self.qty = qty
        self.unit = unit

    def subtotal(self) -> Money:
        return self.unit * self.qty


class Invoice:
    def __init__(self, id: str, customer: str, lines: list[Line]) -> None:
        if not lines:
            raise ValueError("an invoice needs at least one line")
        self.id = id
        self.customer = customer
        self.lines = lines

    def total(self) -> Money:
        running = self.lines[0].subtotal()
        for line in self.lines[1:]:
            running = running + line.subtotal()
        return running
