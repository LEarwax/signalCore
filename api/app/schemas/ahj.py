from pydantic import BaseModel
from typing import List


class AHJOut(BaseModel):
    name: str
    abbreviation: str
    jurisdiction: str
    state: str
    website: str
    min_signal_dbm: float
    design_target_dbm: float
    coverage_pct: float
    critical_areas_pct: float
    freq_bands: List[str]
    battery_hours: float
    highrise_threshold_ft: float
    highrise_coverage_pct: float
    requires_preliminary: bool
    requires_construction_docs: bool
    requires_donor_path_study: bool
    requires_third_party_test: bool
    requires_facp_integration: bool
    requires_signed_plans: bool
    special_requirements: List[str]
    codes: List[str]
    confidence: str
    matched_by: str

    model_config = {"from_attributes": True}


class ClassifyRequest(BaseModel):
    corpus: str
    page_count: int = 1


class BuildingProfileOut(BaseModel):
    floor_count: int
    has_parking: bool
    has_basement: bool
    has_typical_floor: bool
    is_high_rise: bool
    occupancy_type: str
    occupancy_score: float
    construction: List[str]
    engine_type: str
    confidence: float
    rf_params: dict
    notes: List[str]
