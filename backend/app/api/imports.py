import uuid
from dataclasses import dataclass
from decimal import Decimal
from typing import Annotated, Literal, Self

from fastapi import APIRouter, Depends, Form, status
from pydantic import BaseModel, ConfigDict, Field, Json

from app.api.rejections import rejection_responses
from app.api.statements import ReaderDependency
from app.api.uploads import UploadDependency
from app.core.cas_parser import StatementUpload
from app.core.database import SessionDependency
from app.ledger.reconciliation import Action, SchemePlan
from app.ledger.statement_commit import (
    CommitOutcome,
    CommittedImport,
    DecisionsNeeded,
    StatementCommit,
    commit_atomically,
)

router = APIRouter()


class ImportReceipt(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    outcome: Literal["committed"]
    import_id: uuid.UUID
    positions: int
    transactions: int

    @classmethod
    def of(cls, committed: CommittedImport) -> Self:
        return cls(
            outcome="committed",
            import_id=committed.import_id,
            positions=committed.positions,
            transactions=committed.transactions,
        )


class Mismatch(BaseModel):
    """A Scheme whose printed closing units differ from the units the ledger would derive."""

    model_config = ConfigDict(strict=True, frozen=True)

    holding: str
    scheme: str
    institution: str
    folio: str
    printed_units: Decimal
    derived_units: Decimal
    delta: Decimal

    @classmethod
    def of(cls, plan: SchemePlan) -> Self:
        return cls(
            holding=plan.holding.key,
            scheme=plan.scheme.scheme,
            institution=plan.folio.amc,
            folio=plan.folio.folio,
            printed_units=plan.scheme.close,
            derived_units=plan.derived_units,
            delta=plan.delta,
        )


class DecisionsRequired(BaseModel):
    """Nothing was saved. Commit again with an Action for every mismatch."""

    model_config = ConfigDict(strict=True, frozen=True)

    outcome: Literal["needs_decisions"]
    mismatches: list[Mismatch]

    @classmethod
    def of(cls, needed: DecisionsNeeded) -> Self:
        return cls(
            outcome="needs_decisions", mismatches=[Mismatch.of(plan) for plan in needed.mismatches]
        )


ImportOutcome = Annotated[ImportReceipt | DecisionsRequired, Field(discriminator="outcome")]


@dataclass(frozen=True)
class ImportRequest:
    upload: StatementUpload
    decisions: dict[str, Action]


def read_import_request(
    upload: UploadDependency,
    decisions: Annotated[
        Json[dict[str, Action]] | None,
        Form(description="JSON object mapping each mismatch's holding to an Action"),
    ] = None,
) -> ImportRequest:
    return ImportRequest(upload, decisions or {})


ImportRequestDependency = Annotated[ImportRequest, Depends(read_import_request)]


@router.post(  # type: ignore[misc]  # FastAPI decorators are typed with Any
    "/imports",
    operation_id="commitImport",
    response_model=ImportOutcome,
    responses=rejection_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_409_CONFLICT,
        status.HTTP_413_CONTENT_TOO_LARGE,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def commit_import(
    request: ImportRequestDependency, read_statement: ReaderDependency, session: SessionDependency
) -> ImportReceipt | DecisionsRequired:
    """Parse a statement PDF and add it to the ledger. The PDF itself is not kept.

    If any Scheme's closing units disagree with the ledger, nothing is saved and the
    mismatches come back; commit again with a decision for each (ADR 0027).
    """
    upload = request.upload
    commit = StatementCommit(read_statement(upload), upload.fingerprint(), request.decisions)
    return _response(commit_atomically(session, commit))


def _response(outcome: CommitOutcome) -> ImportReceipt | DecisionsRequired:
    match outcome:
        case CommittedImport():
            return ImportReceipt.of(outcome)
        case DecisionsNeeded():
            return DecisionsRequired.of(outcome)
