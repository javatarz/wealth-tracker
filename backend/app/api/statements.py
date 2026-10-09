from collections.abc import Callable
from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.rejections import rejection_responses
from app.api.uploads import UploadDependency
from app.core.cas_parser import StatementUpload, parse_cas_pdf
from app.core.statement_preview import StatementPreview

router = APIRouter()

StatementReader = Callable[[StatementUpload], StatementPreview]


def get_statement_reader() -> StatementReader:
    return parse_cas_pdf


ReaderDependency = Annotated[StatementReader, Depends(get_statement_reader)]


@router.post(  # type: ignore[misc]  # FastAPI decorators are typed with Any
    "/statements/preview",
    operation_id="previewStatement",
    responses=rejection_responses(status.HTTP_400_BAD_REQUEST, status.HTTP_413_CONTENT_TOO_LARGE),
)
def preview_statement(
    upload: UploadDependency, read_statement: ReaderDependency
) -> StatementPreview:
    """Parse a statement PDF and return its contents. Nothing is stored."""
    return read_statement(upload)
