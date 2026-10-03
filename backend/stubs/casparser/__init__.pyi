# Local stub: casparser ships without py.typed. Only the API we call is declared.
from typing import IO, Literal

__version__: str

def read_cas_pdf(
    filename: str | IO[bytes],
    password: str,
    output: Literal["json"],
    sort_transactions: bool = True,
) -> str: ...
