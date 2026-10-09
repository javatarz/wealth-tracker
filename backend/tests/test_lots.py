from datetime import date
from decimal import Decimal

from app.ledger.models import Lot, Transaction


def lot(units: str, cost: str) -> Lot:
    transaction = Transaction(date=date(2024, 4, 1), units=Decimal(units))
    return Lot.acquired_by(transaction, Decimal(cost))


def test_partial_consumption_releases_proportional_cost() -> None:
    parcel = lot("10.000", "1000.00")

    left_to_take = parcel.consume(Decimal("2.500"))

    assert left_to_take == Decimal("0.000")
    assert (parcel.remaining_units, parcel.remaining_cost) == (Decimal("7.500"), Decimal("750.00"))


def test_consuming_more_than_the_lot_empties_it_and_returns_the_rest() -> None:
    parcel = lot("3.000", "100.00")

    left_to_take = parcel.consume(Decimal("5.000"))

    assert left_to_take == Decimal("2.000")
    assert (parcel.remaining_units, parcel.remaining_cost) == (Decimal("0.000"), Decimal("0.00"))


def test_an_empty_lot_takes_nothing() -> None:
    parcel = lot("3.000", "100.00")
    parcel.consume(Decimal("3.000"))

    assert parcel.consume(Decimal("1.000")) == Decimal("1.000")
