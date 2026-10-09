from datetime import date
from decimal import Decimal
from uuid import uuid4

from app.ledger.models import Account, Instrument, Position, Transaction
from app.ledger.valuation import net_worth_series, position_value


def transaction(units: str, price: str, on: date) -> Transaction:
    return Transaction(
        date=on,
        kind="PURCHASE",
        units=Decimal(units),
        nav=Decimal(price),
    )


def position(*transactions: Transaction) -> Position:
    account = Account(household_member_id=uuid4(), institution="X", number="1", kind="mf_folio")
    instrument = Instrument(kind="mutual_fund", identity="k", name="N", asset_class="equity")
    position = Position(id=uuid4(), account=account, instrument=instrument)
    position.transactions = list(transactions)
    return position


def test_value_is_units_times_the_latest_price() -> None:
    held = position(
        transaction("10.000", "100.00", date(2024, 1, 1)),
        transaction("5.000", "120.00", date(2024, 2, 1)),
    )

    assert position_value(held) == Decimal("1800.00")


def test_series_carries_the_value_forward_between_purchases() -> None:
    held = position(
        transaction("10.000", "100.00", date(2024, 1, 1)),
        transaction("5.000", "120.00", date(2024, 2, 1)),
    )

    assert net_worth_series([held]) == [
        (date(2024, 1, 1), Decimal("1000.00")),
        (date(2024, 2, 1), Decimal("1800.00")),
    ]


def test_series_sums_positions_on_the_dates_they_change() -> None:
    first = position(transaction("10.000", "100.00", date(2024, 1, 1)))
    second = position(
        transaction("2.000", "50.00", date(2024, 1, 1)),
        transaction("1.000", "80.00", date(2024, 2, 1)),
    )

    assert net_worth_series([first, second]) == [
        (date(2024, 1, 1), Decimal("1100.00")),
        (date(2024, 2, 1), Decimal("1240.00")),
    ]


def test_a_position_with_no_transactions_contributes_nothing() -> None:
    assert (position_value(position()), net_worth_series([position()])) == (Decimal("0.00"), [])
