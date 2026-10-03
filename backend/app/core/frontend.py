from starlette.exceptions import HTTPException
from starlette.responses import Response
from starlette.staticfiles import StaticFiles
from starlette.status import HTTP_404_NOT_FOUND
from starlette.types import Scope

INDEX_PAGE = "index.html"


class SPAStaticFiles(StaticFiles):
    """Serves the built frontend; unknown non-API paths without a file extension get index.html
    so client-side routes survive a reload."""

    async def get_response(self, path: str, scope: Scope) -> Response:
        try:
            return await super().get_response(path, scope)
        except HTTPException as exc:
            _reraise_unless_client_route(exc, path)
        return await super().get_response(INDEX_PAGE, scope)


def _reraise_unless_client_route(exc: HTTPException, path: str) -> None:
    if exc.status_code != HTTP_404_NOT_FOUND or not _is_client_route(path):
        raise exc


def _is_client_route(path: str) -> bool:
    if path == "api" or path.startswith("api/"):
        return False
    return "." not in path.rsplit("/", 1)[-1]
