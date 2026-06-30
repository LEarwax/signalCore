"""
main.py — signalCore FastAPI application factory
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.routers import projects, ahj, packets, share


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Run Alembic migrations on startup
    async with engine.begin() as conn:
        # In dev: auto-create tables; in prod use alembic upgrade head
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="signalCore API",
    description="ERRCS engineering SaaS — auto-generates AHJ submittal packets from floor plan PDFs",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.WEB_URL],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(ahj.router)
app.include_router(packets.router)
app.include_router(share.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
