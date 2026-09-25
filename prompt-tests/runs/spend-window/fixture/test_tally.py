from datetime import date

from tally import Expense, by_category, render


def rows():
    return [
        Expense("a", date(2026, 1, 1), "food", 1000, ""),
        Expense("b", date(2026, 1, 2), "housing", 5000, ""),
        Expense("c", date(2026, 1, 3), "food", 250, "snack"),
    ]


def test_categories_are_summed():
    assert dict(by_category(rows())) == {"food": 1250, "housing": 5000}


def test_refunds_reduce_a_category():
    refunded = rows() + [Expense("d", date(2026, 1, 4), "food", -250, "returned")]
    assert by_category(refunded)["food"] == 1000


def test_total_line_is_the_sum_of_every_category():
    out = render(by_category(rows()), None).splitlines()
    assert out[-1].split()[-1] == "62.50"
