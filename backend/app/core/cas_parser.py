"""Parse CAMS/KFintech consolidated account statements with casparser (ADR 0013).

The PDF is parsed in memory and never written to disk (ADR 0019). Only the
folio/scheme/transaction tree is returned; investor contact details and PAN
are dropped at this boundary.
"""

import io
import logging
from dataclasses import dataclass
from importlib.metadata import version

import casparser
from casparser.exceptions import CASParseError, IncorrectPasswordError
from pydantic import BaseModel, ValidationError

from app.core.statement_preview import (
    IssuerProbe,
    ParsedStatement,
    ParserInfo,
    StatementParseError,
    StatementPreview,
)

logger = logging.getLogger(__name__)

PARSER = ParserInfo(name="casparser", version=version("casparser"))
_PDF_SIGNATURE = b"%PDF-"
_DAMAGED_PDF_PREFIX = "Unhandled error while opening PDF"
_SUPPORTED_ISSUERS = frozenset({"CAMS", "KFINTECH"})


@dataclass(frozen=True)
class StatementUpload:
    content: bytes
    password: str

    def ensure_pdf(self) -> None:
        if not self.content.startswith(_PDF_SIGNATURE):
            raise StatementParseError.not_a_pdf()

    def password_error(self) -> StatementParseError:
        if self.password:
            return StatementParseError.incorrect_password()
        return StatementParseError.password_required()


def parse_cas_pdf(upload: StatementUpload) -> StatementPreview:
    upload.ensure_pdf()
    output = _run_casparser(upload)
    _ensure_supported_issuer(output)
    return _validate(ParsedStatement, output).previewed_by(PARSER)


def _run_casparser(upload: StatementUpload) -> str:
    try:
        return casparser.read_cas_pdf(io.BytesIO(upload.content), upload.password, output="json")
    except IncorrectPasswordError as exc:
        raise upload.password_error() from exc
    except CASParseError as exc:
        raise _unreadable(exc) from exc
    except Exception as exc:
        logger.warning("casparser crashed: %s", type(exc).__name__)
        raise StatementParseError.parse_failed(PARSER) from exc


def _unreadable(exc: CASParseError) -> StatementParseError:
    if str(exc).startswith(_DAMAGED_PDF_PREFIX):
        return StatementParseError.damaged_pdf()
    return StatementParseError.unrecognised_statement()


def _ensure_supported_issuer(output: str) -> None:
    issuer = _validate(IssuerProbe, output).file_type
    if issuer not in _SUPPORTED_ISSUERS:
        raise StatementParseError.unsupported_statement(issuer)


def _validate[M: BaseModel](model: type[M], output: str) -> M:
    try:
        return model.model_validate_json(output)
    except ValidationError as exc:
        logger.warning("casparser output did not match the expected shape")
        raise StatementParseError.parse_failed(PARSER) from exc
