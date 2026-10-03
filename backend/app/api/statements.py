from typing import Annotated, Literal

from fastapi import APIRouter, File, Form, Response, UploadFile
from pydantic import BaseModel, ConfigDict

from app.core.cas_parser import ParseErrorCode, StatementParseError, StatementPreview, parse_cas_pdf

router = APIRouter()

MAX_STATEMENT_BYTES = 20 * 1024 * 1024

StatementErrorCode = ParseErrorCode | Literal["file_too_large"]


class StatementError(BaseModel):
    model_config = ConfigDict(strict=True)

    code: StatementErrorCode
    message: str


_ERROR_RESPONSES: dict[int | str, dict[str, type[StatementError]]] = {
    400: {"model": StatementError},
    413: {"model": StatementError},
}


@router.post(  # type: ignore[misc]  # FastAPI decorators are typed with Any
    "/statements/preview",
    operation_id="previewStatement",
    response_model=StatementPreview,
    responses=_ERROR_RESPONSES,
)
def preview_statement(
    file: Annotated[UploadFile, File(description="CAMS/KFintech consolidated account statement")],
    password: Annotated[str, Form()] = "",
) -> StatementPreview | Response:
    """Parse a statement PDF and return its contents. Nothing is stored."""
    content = file.file.read(MAX_STATEMENT_BYTES + 1)
    if len(content) > MAX_STATEMENT_BYTES:
        return _error(413, "file_too_large", "Statements larger than 20 MB aren't accepted.")
    try:
        return parse_cas_pdf(content, password)
    except StatementParseError as exc:
        return _error(400, exc.code, exc.message)


def _error(status: int, code: StatementErrorCode, message: str) -> Response:
    body = StatementError(code=code, message=message).model_dump_json()
    return Response(content=body, status_code=status, media_type="application/json")
