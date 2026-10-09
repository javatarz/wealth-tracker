import uuid
from typing import Self

from fastapi import APIRouter, status
from pydantic import BaseModel, ConfigDict

from app.api.rejections import rejection_responses
from app.api.statements import ReaderDependency
from app.api.uploads import UploadDependency
from app.core.database import SessionDependency
from app.ledger.statement_commit import CommittedImport, commit_atomically

router = APIRouter()


class ImportReceipt(BaseModel):
    model_config = ConfigDict(strict=True, frozen=True)

    import_id: uuid.UUID
    positions: int
    transactions: int

    @classmethod
    def of(cls, committed: CommittedImport) -> Self:
        return cls(
            import_id=committed.import_id,
            positions=committed.positions,
            transactions=committed.transactions,
        )


@router.post(  # type: ignore[misc]  # FastAPI decorators are typed with Any
    "/imports",
    operation_id="commitImport",
    status_code=status.HTTP_201_CREATED,
    responses=rejection_responses(
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_409_CONFLICT,
        status.HTTP_413_CONTENT_TOO_LARGE,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
    ),
)
def commit_import(
    upload: UploadDependency, read_statement: ReaderDependency, session: SessionDependency
) -> ImportReceipt:
    """Parse a statement PDF and add it to the ledger. The PDF itself is not kept."""
    statement = read_statement(upload)
    return ImportReceipt.of(commit_atomically(session, statement, upload.fingerprint()))
