import json
from decimal import Decimal
from importlib.metadata import version

import casparser
import pytest

from app.core.cas_parser import StatementParseError, parse_cas_pdf
from tests.conftest import FIXTURES, MOCK_CAS_PASSWORD


def _casparser_json(**overrides: object) -> str:
    golden = json.loads((FIXTURES / "mock_casparser_output.json").read_text())
    return json.dumps(golden | overrides)


def test_casparser_output_matches_golden_fixture() -> None:
    raw = casparser.read_cas_pdf(str(FIXTURES / "mock_cams_cas.pdf"), "", output="json")

    golden = json.loads((FIXTURES / "mock_casparser_output.json").read_text())
    assert json.loads(raw) == golden


def test_parses_folios_schemes_and_transactions(mock_cas_pdf: bytes) -> None:
    preview = parse_cas_pdf(mock_cas_pdf, "")

    assert preview.file_type == "CAMS"
    assert preview.cas_type == "DETAILED"
    assert preview.statement_period.from_ == "01-Apr-2024"
    assert [(f.folio, f.amc) for f in preview.folios] == [
        ("1234567890", "HDFC Mutual Fund"),
        ("1234567890", "ICICI Prudential Mutual Fund"),
        ("9876543210", "SBI Mutual Fund"),
    ]
    scheme = preview.folios[0].schemes[0]
    assert scheme.scheme == "HDFC Top 200 Fund - Direct Plan - Growth"
    assert scheme.close == Decimal("1830.270")
    first = scheme.transactions[0]
    assert (first.type, first.units, first.balance) == (
        "PURCHASE",
        Decimal("1136.067"),
        Decimal("1136.067"),
    )
    assert preview.parse_warnings == []


def test_records_parser_version(mock_cas_pdf: bytes) -> None:
    preview = parse_cas_pdf(mock_cas_pdf, "")

    assert preview.parser.name == "casparser"
    assert preview.parser.version == version("casparser")


def test_drops_investor_contact_details_and_pan(mock_cas_pdf: bytes) -> None:
    body = parse_cas_pdf(mock_cas_pdf, "").model_dump_json(by_alias=True)

    for pii in ("JOHN DOE", "john.doe@example.com", "ABCDE1234F", "+919999999999"):
        assert pii not in body


def test_surfaces_parse_warnings(mock_cas_pdf: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    warning = "Balance mismatch in HDFC Top 200 Fund on 2024-05-17"
    monkeypatch.setattr(
        casparser, "read_cas_pdf", lambda *_a, **_k: _casparser_json(parse_warnings=[warning])
    )

    assert parse_cas_pdf(mock_cas_pdf, "").parse_warnings == [warning]


@pytest.mark.parametrize(
    ("password", "code"),
    [("", "password_required"), ("wrong", "incorrect_password")],
)
def test_rejects_missing_or_wrong_password(
    encrypted_mock_cas_pdf: bytes, password: str, code: str
) -> None:
    with pytest.raises(StatementParseError) as exc:
        parse_cas_pdf(encrypted_mock_cas_pdf, password)

    assert exc.value.code == code


def test_opens_encrypted_statement_with_password(encrypted_mock_cas_pdf: bytes) -> None:
    preview = parse_cas_pdf(encrypted_mock_cas_pdf, MOCK_CAS_PASSWORD)

    assert len(preview.folios) == 3


@pytest.mark.parametrize("content", [b"", b"hello", b"PK\x03\x04zip"])
def test_rejects_non_pdf(content: bytes) -> None:
    with pytest.raises(StatementParseError) as exc:
        parse_cas_pdf(content, "")

    assert exc.value.code == "not_a_pdf"


def test_rejects_damaged_pdf() -> None:
    with pytest.raises(StatementParseError) as exc:
        parse_cas_pdf(b"%PDF-1.7\nnot really a pdf", "")

    assert exc.value.code == "not_a_pdf"


def test_rejects_pdf_that_is_not_a_cas(blank_pdf: bytes) -> None:
    with pytest.raises(StatementParseError) as exc:
        parse_cas_pdf(blank_pdf, "")

    assert exc.value.code == "unrecognised_statement"
    assert "Re-saved" in exc.value.message


def test_rejects_demat_statements(mock_cas_pdf: bytes, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        casparser, "read_cas_pdf", lambda *_a, **_k: _casparser_json(file_type="NSDL")
    )

    with pytest.raises(StatementParseError) as exc:
        parse_cas_pdf(mock_cas_pdf, "")

    assert exc.value.code == "unsupported_statement"


def test_parser_crash_is_a_parse_failure(
    mock_cas_pdf: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    def crash(*_a: object, **_k: object) -> str:
        raise IndexError("list index out of range")

    monkeypatch.setattr(casparser, "read_cas_pdf", crash)

    with pytest.raises(StatementParseError) as exc:
        parse_cas_pdf(mock_cas_pdf, "")

    assert exc.value.code == "parse_failed"


def test_unexpected_parser_output_is_a_parse_failure(
    mock_cas_pdf: bytes, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(casparser, "read_cas_pdf", lambda *_a, **_k: _casparser_json(folios=None))

    with pytest.raises(StatementParseError) as exc:
        parse_cas_pdf(mock_cas_pdf, "")

    assert exc.value.code == "parse_failed"
