"""The growth rate a Goal's Projection uses, per its chosen Projection Strategy (ADR 0009).

`None` means insufficient data — the UI shows a grey badge rather than a made-up number.
The strategies live in a lookup keyed by name, so a new one is added by adding an entry.
"""

from collections.abc import Callable, Sequence
from datetime import date
from decimal import Decimal

from app.goals.dates import years_before
from app.goals.models import CAGR, TRAILING_WINDOW, Goal
from app.goals.progress import value_asof
from app.ledger.models import PAISE, ZERO, Position

AT_RISK_TOLERANCE = Decimal("0.10")

# The goal-detail badge grades a shortfall against its target: green above target,
# amber within the tolerance below it, red beyond that.
Grade = Callable[[Decimal], bool]
GRADES: tuple[tuple[Grade, str], ...] = (
    (lambda shortfall: shortfall < 0, "exceeded"),
    (lambda shortfall: shortfall == 0, "on_track"),
    (lambda shortfall: shortfall <= AT_RISK_TOLERANCE, "at_risk"),
    (lambda _shortfall: True, "off_track"),
)

Strategy = Callable[[Goal, Sequence[Position], date], Decimal | None]


def _cagr(goal: Goal, _positions: Sequence[Position], _as_of: date) -> Decimal | None:
    return goal.cagr_rate


def _trailing_window(goal: Goal, positions: Sequence[Position], as_of: date) -> Decimal | None:
    return _trailing_rate(positions, as_of, goal.trailing_window_years)


STRATEGIES: dict[str, Strategy] = {CAGR: _cagr, TRAILING_WINDOW: _trailing_window}


def rate_for(goal: Goal, positions: Sequence[Position], as_of: date) -> Decimal | None:
    """None when no strategy is chosen; a strategy may still find insufficient data."""
    strategy = STRATEGIES.get(goal.projection_strategy or "")
    if strategy is None:
        return None
    return strategy(goal, positions, as_of)


def _trailing_rate(positions: Sequence[Position], as_of: date, years: int | None) -> Decimal | None:
    if not years or years <= 0:
        return None
    start = years_before(as_of, years)
    beginning = sum((value_asof(position, start) for position in positions), ZERO)
    ending = sum((value_asof(position, as_of) for position in positions), ZERO)
    if beginning <= ZERO or ending <= ZERO:
        return None
    return _annualise(ending / beginning, years)


def _annualise(ratio: Decimal, years: int) -> Decimal:
    return (ratio ** (Decimal(1) / years) - 1).quantize(PAISE)


def status_for(projected: Decimal, target: Decimal) -> str:
    """exceeded / on_track / at_risk / off_track / insufficient_data, per the badge."""
    if target <= ZERO:
        return "insufficient_data"
    shortfall = (target - projected) / target
    return next(grade for matches, grade in GRADES if matches(shortfall))
