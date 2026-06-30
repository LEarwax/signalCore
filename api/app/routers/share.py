from fastapi import APIRouter, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.core.database import get_db

router = APIRouter(prefix="/api/share", tags=["share"])


@router.get("/{token}")
async def get_shared_packet(token: str, db: AsyncSession = Depends(get_db)):
    # TODO: look up ShareableLink by token, return snapshot_data (no auth required)
    raise HTTPException(status_code=404, detail="Link not found")
