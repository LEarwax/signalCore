"""
main.py — signalCore FastAPI application factory
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import engine, Base
from app.routers import projects, ahj, packets, share, uploads


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Migrations run via start.sh before uvicorn starts.
    # Lifespan handles seeding only.
    import logging
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.services.ahj_service import seed_ahj_records

    logger = logging.getLogger("signalcore.startup")
    logging.basicConfig(level=logging.INFO)

    try:
        logger.info("Seeding AHJ records...")
        async with AsyncSession(engine) as session:
            await seed_ahj_records(session)
        logger.info("Seeding complete.")
    except Exception as e:
        logger.error("Seeding failed: %s", e, exc_info=True)
        # Non-fatal — app still starts

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
app.include_router(uploads.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
