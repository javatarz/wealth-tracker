"""Why a statement upload was turned away, in terms the browser can show."""

from typing import Literal

ParseErrorCode = Literal[
    "not_a_pdf",
    "password_required",
    "incorrect_password",
    "unrecognised_statement",
    "unsupported_statement",
    "parse_failed",
]

ManualEntryCode = Literal[
    "unexpected_type",
    "future_date",
    "non_positive_units",
    "negative_cost",
    "cost_required",
    "position_not_found",
]

IncomeCode = Literal[
    "unexpected_income_type",
    "non_positive_amount",
    "invalid_tax",
    "reinvestment_not_supported",
    "nav_required",
]

RejectionCode = (
    ParseErrorCode
    | ManualEntryCode
    | IncomeCode
    | Literal["file_too_large", "already_imported", "commit_failed"]
)


class StatementRejectedError(Exception):
    def __init__(self, code: RejectionCode, message: str) -> None:
        super().__init__(message)
        self.code: RejectionCode = code
        self.message = message
