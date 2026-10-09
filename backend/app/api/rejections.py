from fastapi import Request, Response, status
from pydantic import BaseModel, ConfigDict

from app.core.statement_rejection import RejectionCode, StatementRejectedError

_STATUS_BY_CODE: dict[RejectionCode, int] = {
    "file_too_large": status.HTTP_413_CONTENT_TOO_LARGE,
    "already_imported": status.HTTP_409_CONFLICT,
    "commit_failed": status.HTTP_500_INTERNAL_SERVER_ERROR,
    "position_not_found": status.HTTP_404_NOT_FOUND,
}


class StatementError(BaseModel):
    model_config = ConfigDict(strict=True)

    code: RejectionCode
    message: str


def rejection_responses(*status_codes: int) -> dict[int | str, dict[str, type[StatementError]]]:
    return {status_code: {"model": StatementError} for status_code in status_codes}


def rejection_response(rejection: StatementRejectedError) -> Response:
    error = StatementError(code=rejection.code, message=rejection.message)
    return Response(
        content=error.model_dump_json(),
        status_code=_STATUS_BY_CODE.get(rejection.code, status.HTTP_400_BAD_REQUEST),
        media_type="application/json",
    )


def handle_rejection(_request: Request, exc: Exception) -> Response:
    if not isinstance(exc, StatementRejectedError):
        raise exc
    return rejection_response(exc)
