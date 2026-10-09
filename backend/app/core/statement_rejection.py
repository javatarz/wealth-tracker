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

RejectionCode = ParseErrorCode | Literal["file_too_large", "already_imported", "commit_failed"]


class StatementRejectedError(Exception):
    def __init__(self, code: RejectionCode, message: str) -> None:
        super().__init__(message)
        self.code: RejectionCode = code
        self.message = message
