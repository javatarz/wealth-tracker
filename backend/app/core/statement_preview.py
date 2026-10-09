"""The read-only statement preview returned to the browser, and why a parse failed."""

from datetime import date
from decimal import Decimal
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field

from app.core.statement_rejection import StatementRejectedError

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


class IssuerProbe(_Model):
    """Just enough of the parser output to tell which issuer produced the statement."""

    file_type: str


class ParsedStatement(_Model):
    statement_period: StatementPeriod
    file_type: Literal["CAMS", "KFINTECH"]
    cas_type: Literal["DETAILED", "SUMMARY"]
    folios: list[Folio]
    parse_warnings: list[str]

    def previewed_by(self, parser: ParserInfo) -> "StatementPreview":
        return StatementPreview(
            statement_period=self.statement_period,
            file_type=self.file_type,
            cas_type=self.cas_type,
            folios=self.folios,
            parse_warnings=self.parse_warnings,
            parser=parser,
        )


class StatementPreview(ParsedStatement):
    parser: ParserInfo


class StatementParseError(StatementRejectedError):
    @classmethod
    def not_a_pdf(cls) -> Self:
        return cls("not_a_pdf", "This file isn't a PDF.")

    @classmethod
    def damaged_pdf(cls) -> Self:
        return cls("not_a_pdf", "This PDF is damaged and can't be opened.")

    @classmethod
    def password_required(cls) -> Self:
        return cls("password_required", "This statement is password-protected.")

    @classmethod
    def incorrect_password(cls) -> Self:
        return cls("incorrect_password", "That password didn't open the statement.")

    @classmethod
    def unrecognised_statement(cls) -> Self:
        return cls(
            "unrecognised_statement",
            "This file isn't an original CAMS or KFintech Consolidated Account Statement. "
            "Re-saved or printed copies, MFCentral statements and single-AMC statements "
            "can't be read — download the CAS again from CAMS or KFintech.",
        )

    @classmethod
    def unsupported_statement(cls, issuer: str) -> Self:
        return cls(
            "unsupported_statement",
            f"{issuer} demat statements aren't supported yet. "
            "Upload a CAMS or KFintech Consolidated Account Statement.",
        )

    @classmethod
    def parse_failed(cls, parser: ParserInfo) -> Self:
        return cls(
            "parse_failed",
            "The statement was recognised but couldn't be read. "
            f"This may be a {parser.name} {parser.version} limitation.",
        )
