from fastapi import APIRouter, Query

router = APIRouter(prefix="/api/ahj", tags=["ahj"])


@router.get("/lookup")
async def lookup_ahj(address: str = Query(..., description="Full project address")):
    # TODO: port core/ahj.py lookup logic here
    return {"message": "AHJ lookup not yet implemented", "address": address}
