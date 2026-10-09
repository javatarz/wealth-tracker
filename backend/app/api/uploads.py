from typing import Annotated

from fastapi import Depends, File, Form, UploadFile

from app.core.cas_parser import StatementUpload
from app.core.statement_rejection import StatementRejectedError

MAX_STATEMENT_MB = 20
MAX_STATEMENT_BYTES = MAX_STATEMENT_MB * 1024 * 1024


def read_statement_upload(
    file: Annotated[UploadFile, File(description="CAMS/KFintech consolidated account statement")],
    password: Annotated[str, Form()] = "",
) -> StatementUpload:
    content = file.file.read(MAX_STATEMENT_BYTES + 1)
    if len(content) > MAX_STATEMENT_BYTES:
        raise StatementRejectedError(
            "file_too_large", f"Statements larger than {MAX_STATEMENT_MB} MB aren't accepted."
        )
    return StatementUpload(content, password)


UploadDependency = Annotated[StatementUpload, Depends(read_statement_upload)]
