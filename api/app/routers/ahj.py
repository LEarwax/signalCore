"""
routers/ahj.py — AHJ lookup and building classifier endpoints.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_engineer
from app.core.database import get_db
from app.models.engineer import Engineer
from app.schemas.ahj import AHJOut, BuildingProfileOut, ClassifyRequest
from app.services.ahj_service import lookup_ahj
from app.services.classifier import classifier

router = APIRouter(prefix="/api/ahj", tags=["ahj"])


@router.get("/lookup", response_model=AHJOut)
async def ahj_lookup(
    address: str = Query(..., description="Full project address, e.g. '123 Main St, San Jose, CA 95101'"),
    db: AsyncSession = Depends(get_db),
    _: Engineer = Depends(get_current_engineer),
):
    """
    Return the applicable AHJ profile for a project address.
    Looks up the DB first, falls back to CA/out-of-state defaults.
    """
    profile = await lookup_ahj(address, db)
    return AHJOut(**profile.to_dict())


@router.post("/classify", response_model=BuildingProfileOut)
async def classify_building(
    body: ClassifyRequest,
    _: Engineer = Depends(get_current_engineer),
):
    """
    Classify a building from its combined PDF text corpus.
    Returns engine type, occupancy, floor count, and RF parameters.
    """
    profile = classifier.classify(corpus=body.corpus, page_count=body.page_count)
    return BuildingProfileOut(**profile.to_dict())
