from pydantic import BaseModel
from typing import Optional


class SheetOut(BaseModel):
    id: str
    page_number: int
    label: str
    type: str          # floor_plan | elevation | section | detail | other
    thumbnail_url: Optional[str] = None

    model_config = {"from_attributes": True}


class UploadOut(BaseModel):
    upload_id: str
    filename: str
    page_count: int
    sheets: list[SheetOut]
