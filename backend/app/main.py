from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import benchmarks, health, imports, positions, statements
from app.api.rejections import handle_rejection
from app.core.config import Settings, get_settings
from app.core.frontend import SPAStaticFiles
from app.core.statement_rejection import StatementRejectedError


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="Wealth Tracker", version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(StatementRejectedError, handle_rejection)
    app.include_router(health.router, prefix="/api")
    app.include_router(statements.router, prefix="/api")
    app.include_router(imports.router, prefix="/api")
    app.include_router(positions.router, prefix="/api")
    app.include_router(benchmarks.router, prefix="/api")
    if settings.static_dir is not None:
        app.mount("/", SPAStaticFiles(directory=settings.static_dir, html=True), name="frontend")
    return app


app = create_app()
