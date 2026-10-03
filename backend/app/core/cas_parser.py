"""Parse CAMS/KFintech consolidated account statements with casparser (ADR 0013).

The PDF is parsed in memory and never written to disk (ADR 0019). Only the
folio/scheme/transaction tree is returned; investor contact details and PAN
are dropped at this boundary.
"""

import io
import logging
from datetime import date
from decimal import Decimal
from importlib.metadata import version
from typing import Literal

import casparser
from casparser.exceptions import CASParseError, IncorrectPasswordError, ParserException
from pydantic import BaseModel, ConfigDict, Field, ValidationError

logger = logging.getLogger(__name__)

PARSER_NAME: Literal["casparser"] = "casparser"
PARSER_VERSION = version(PARSER_NAME)

ParseErrorCode = Literal[
    "not_a_pdf",
    "password_required",
    "incorrect_password",
    "unrecognised_statement",
    "unsupported_statement",
    "parse_failed",
]

TransactionType = Literal[
    "PURCHASE",
    "PURCHASE_SIP",
    "REDEMPTION",
    "DIVIDEND_PAYOUT",
    "DIVIDEND_REINVEST",
    "SWITCH_IN",
    "SWITCH_IN_MERGER",
    "SWITCH_OUT",
    "SWITCH_OUT_MERGER",
    "STT_TAX",
    "STAMP_DUTY_TAX",
    "TDS_TAX",
    "SEGREGATION",
    "GIFT_IN",
    "GIFT_OUT",
    "MISC",
    "UNKNOWN",
    "REVERSAL",
]


class _Model(BaseModel):
    model_config = ConfigDict(strict=True, extra="ignore", frozen=True)


class ParserInfo(_Model):
    name: Literal["casparser"]
    version: str


class StatementPeriod(_Model):
    from_: str = Field(alias="from")
    to: str


class Transaction(_Model):
    date: date
    description: str
    type: TransactionType
    amount: Decimal | None
    units: Decimal | None
    nav: Decimal | None
    balance: Decimal | None
    dividend_rate: Decimal | None


class Valuation(_Model):
    date: date
    nav: Decimal
    cost: Decimal | None
    value: Decimal


class Scheme(_Model):
    scheme: str
    isin: str | None
    amfi: str | None
    type: str | None
    rta: str
    rta_code: str
    advisor: str | None
    open: Decimal
    close: Decimal
    close_calculated: Decimal
    valuation: Valuation
    transactions: list[Transaction]


class Folio(_Model):
    folio: str
    amc: str
    schemes: list[Scheme]


class _ParsedCas(_Model):
    statement_period: StatementPeriod
    file_type: Literal["CAMS", "KFINTECH"]
    cas_type: Literal["DETAILED", "SUMMARY"]
    folios: list[Folio]
    parse_warnings: list[str]


class _Issuer(_Model):
    file_type: str


class StatementPreview(_ParsedCas):
    parser: ParserInfo


class StatementParseError(Exception):
    def __init__(self, code: ParseErrorCode, message: str) -> None:
        super().__init__(message)
        self.code: ParseErrorCode = code
        self.message = message


_UNRECOGNISED = (
    "This file isn't an original CAMS or KFintech Consolidated Account Statement. "
    "Re-saved or printed copies, MFCentral statements and single-AMC statements "
    "can't be read — download the CAS again from CAMS or KFintech."
)


def parse_cas_pdf(content: bytes, password: str) -> StatementPreview:
    if not content.startswith(b"%PDF-"):
        raise StatementParseError("not_a_pdf", "This file isn't a PDF.")

    try:
        raw = casparser.read_cas_pdf(io.BytesIO(content), password, output="json")
    except IncorrectPasswordError as exc:
        if password:
            raise StatementParseError(
                "incorrect_password", "That password didn't open the statement."
            ) from exc
        raise StatementParseError(
            "password_required", "This statement is password-protected."
        ) from exc
    except CASParseError as exc:
        if str(exc).startswith("Unhandled error while opening PDF"):
            raise StatementParseError(
                "not_a_pdf", "This PDF is damaged and can't be opened."
            ) from exc
        raise StatementParseError("unrecognised_statement", _UNRECOGNISED) from exc
    except ParserException as exc:
        logger.warning("casparser rejected the statement: %s", type(exc).__name__)
        raise _parse_failed() from exc
    except Exception as exc:
        logger.warning("casparser crashed: %s", type(exc).__name__)
        raise _parse_failed() from exc

    try:
        issuer = _Issuer.model_validate_json(raw).file_type
        if issuer not in ("CAMS", "KFINTECH"):
            raise StatementParseError(
                "unsupported_statement",
                f"{issuer} demat statements aren't supported yet. "
                "Upload a CAMS or KFintech Consolidated Account Statement.",
            )
        parsed = _ParsedCas.model_validate_json(raw)
    except ValidationError as exc:
        logger.warning("casparser output did not match the expected shape")
        raise _parse_failed() from exc

    return StatementPreview(
        statement_period=parsed.statement_period,
        file_type=parsed.file_type,
        cas_type=parsed.cas_type,
        folios=parsed.folios,
        parse_warnings=parsed.parse_warnings,
        parser=ParserInfo(name=PARSER_NAME, version=PARSER_VERSION),
    )


def _parse_failed() -> StatementParseError:
    return StatementParseError(
        "parse_failed",
        "The statement was recognised but couldn't be read. "
        f"This may be a {PARSER_NAME} {PARSER_VERSION} limitation.",
    )
