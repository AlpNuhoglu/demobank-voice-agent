from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import Engine

from app import db
from app.routers import health


def create_app(engine: Engine | None = None) -> FastAPI:
    bind = engine or db.engine

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        db.init_db(bind)
        yield

    app = FastAPI(title="Demo Bank voice agent backend", lifespan=lifespan)
    app.include_router(health.router)
    return app


app = create_app()
