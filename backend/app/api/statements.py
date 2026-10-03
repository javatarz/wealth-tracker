from collections.abc import Callable
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, File, Form, Response, UploadFile, status
from pydantic import BaseModel, ConfigDict

from app.core.cas_parser import StatementUpload, parse_cas_pdf
from app.core.statement_preview import ParseErrorCode, StatementParseError, StatementPreview

router = APIRouter()

MAX_STATEMENT_MB = 20
MAX_STATEMENT_BYTES = MAX_STATEMENT_MB * 1024 * 1024

StatementErrorCode = ParseErrorCode | Literal["file_too_large"]
StatementReader = Callable[[StatementUpload], StatementPreview]


class StatementError(BaseModel):
    model_config = ConfigDict(strict=True)

    code: StatementErrorCode
    message: str

    def as_response(self, status_code: int) -> Response:
        return Response(
            content=self.model_dump_json(),
            status_code=status_code,
            media_type="application/json",
        )


_ERROR_RESPONSES: dict[int | str, dict[str, type[StatementError]]] = {
    status.HTTP_400_BAD_REQUEST: {"model": StatementError},
    status.HTTP_413_CONTENT_TOO_LARGE: {"model": StatementError},
}

_TOO_LARGE = StatementError(
    code="file_too_large",
    message=f"Statements larger than {MAX_STATEMENT_MB} MB aren't accepted.",
)


def get_statement_reader() -> StatementReader:
    return parse_cas_pdf


@router.post(  # type: ignore[misc]  # FastAPI decorators are typed with Any
    "/statements/preview",
    operation_id="previewStatement",
    response_model=StatementPreview,
    responses=_ERROR_RESPONSES,
)
def preview_statement(
    file: Annotated[UploadFile, File(description="CAMS/KFintech consolidated account statement")],
    read_statement: Annotated[StatementReader, Depends(get_statement_reader)],
    password: Annotated[str, Form()] = "",
) -> StatementPreview | Response:
    """Parse a statement PDF and return its contents. Nothing is stored."""
    content = file.file.read(MAX_STATEMENT_BYTES + 1)
    if len(content) > MAX_STATEMENT_BYTES:
        return _TOO_LARGE.as_response(status.HTTP_413_CONTENT_TOO_LARGE)
    try:
        return read_statement(StatementUpload(content=content, password=password))
    except StatementParseError as exc:
        error = StatementError(code=exc.code, message=exc.message)
        return error.as_response(status.HTTP_400_BAD_REQUEST)
