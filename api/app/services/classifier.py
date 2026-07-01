"""
services/classifier.py — Building type classification and engine routing.

Ported from partner's core/classifier.py v1.1.
Weighted keyword scoring with per-category thresholds and negative keywords.
"""

import re
from dataclasses import dataclass, field
from typing import List


# ── ENGINE RF PARAMETERS ──────────────────────────────────────────────────────

ENGINE_RF = {
    'single_floor': {'R_OFFICE': 35, 'R_WH': 60, 'N_OFFICE': 2.8, 'N_WH': 2.2},
    'parking':      {'R_OFFICE': 75, 'R_WH': 75, 'N_OFFICE': 1.8, 'N_WH': 1.8},
    'healthcare':   {'R_OFFICE': 20, 'R_WH': 30, 'N_OFFICE': 3.5, 'N_WH': 3.0},
    'multi_floor':  {'R_OFFICE': 35, 'R_WH': 55, 'N_OFFICE': 2.8, 'N_WH': 2.3},
    'high_rise':    {'R_OFFICE': 40, 'R_WH': 60, 'N_OFFICE': 2.6, 'N_WH': 2.2},
    'hotel':        {'R_OFFICE': 30, 'R_WH': 45, 'N_OFFICE': 3.2, 'N_WH': 2.5},
}


# ── OCCUPANCY KEYWORD TABLES ──────────────────────────────────────────────────
# Each entry: (keyword, weight)
# weight 1.0 = definitive, 0.9 = very strong, 0.7 = strong, 0.5 = moderate
# threshold = minimum total weighted score to classify as this type

OCCUPANCY_WEIGHTED = {

    'warehouse': {
        'keywords': [
            ('FORKLIFT',         1.0), ('RACKING',           1.0),
            ('PALLET',           1.0), ('HIGH BAY',          1.0),
            ('LOADING DOCK',     1.0), ('OVERHEAD DOOR',     0.95),
            ('DOCK LEVELER',     1.0), ('DOCK',              0.9),
            ('RECEIVING',        0.9), ('LUBE',              0.9),
            ('FLEET',            0.85), ('DISPATCH',         0.85),
            ('HAULING',          0.85), ('FREIGHT',          0.85),
            ('MECH. BAY',        0.85), ('SERVICE BAY',      0.9),
            ('MAINTENANCE',      0.75), ('PARTS',            0.7),
            ('SHOP',             0.65), ('WAREHOUSE',        0.8),
            ('STORAGE',          0.55), ('PEMB',             0.6),
            ('OPEN',             0.4),  ('MEZZANINE',        0.6),
            ('SERVICES',         0.45), ('FLEET',            0.8),
        ],
        'negative':  ['PARKING STALL', 'GUEST ROOM', 'PATIENT ROOM', 'CLASSROOM'],
        'threshold': 0.80,
    },

    'office': {
        'keywords': [
            ('OPEN OFFICE',      1.0), ('CUBICLE',           0.95),
            ('CONFERENCE ROOM',  0.95), ('RECEPTION',        0.9),
            ('SERVER ROOM',      0.9), ('COPY ROOM',         0.9),
            ('WORKSTATION',      0.85), ('IT ROOM',          0.85),
            ('HUDDLE',           0.85), ('HUDDLE ROOM',      0.9),
            ('BREAK ROOM',       0.8), ('OPEN PLAN',         0.85),
            ('LOBBY',            0.6), ('EXECUTIVE',         0.75),
            ('OFFICE',           0.45),
        ],
        'negative':  ['PARKING STALL', 'PATIENT ROOM', 'GUEST ROOM'],
        'threshold': 0.80,
    },

    'hotel': {
        'keywords': [
            ('GUEST ROOM',       1.0), ('GUESTROOM',         1.0),
            ('HOUSEKEEPING',     0.95), ('FRONT DESK',       0.95),
            ('GUEST SUITE',      0.95), ('LINEN ROOM',       0.9),
            ('LINEN CLOSET',     0.85), ('AMENITY',          0.75),
            ('BALLROOM',         0.9), ('FITNESS CENTER',    0.85),
            ('BANQUET',          0.85), ('SPA',              0.75),
        ],
        'negative':  ['PATIENT ROOM', 'PARKING STALL', 'FORKLIFT', 'RECEIVING'],
        'threshold': 0.90,
    },

    'healthcare': {
        'keywords': [
            ('PATIENT ROOM',     1.0), ('NURSE STATION',     1.0),
            ('ICU',              1.0), ('OPERATING ROOM',    1.0),
            ('EXAM ROOM',        0.95), ('TREATMENT ROOM',   0.95),
            ('EMERGENCY ROOM',   0.95), ('RADIOLOGY',        0.9),
            ('PHARMACY',         0.85), ('TRAUMA',           0.95),
            ('STERILIZATION',    0.9), ('SURGICAL',          0.9),
            ('WAITING ROOM',     0.65), ('CLINIC',           0.75),
            ('MEDICAL',          0.6),
        ],
        'negative':  ['GUEST ROOM', 'PARKING STALL', 'LOADING DOCK'],
        'threshold': 0.90,
    },

    'residential': {
        'keywords': [
            ('BEDROOM',          1.0), ('MASTER BEDROOM',    1.0),
            ('LIVING ROOM',      0.95), ('DINING ROOM',      0.9),
            ('DWELLING UNIT',    1.0), ('1 BEDROOM',         0.95),
            ('2 BEDROOM',        0.95), ('3 BEDROOM',        0.95),
            ('STUDIO UNIT',      0.9), ('MASTER BATH',       0.85),
            ('KITCHEN',          0.75), ('WALK-IN CLOSET',   0.8),
            ('UNIT',             0.45),
        ],
        'negative':  ['GUEST ROOM', 'PATIENT ROOM', 'FORKLIFT', 'LOADING DOCK'],
        'threshold': 0.90,
    },

    'retail': {
        'keywords': [
            ('SALES FLOOR',      1.0), ('MERCHANDISE',       0.95),
            ('FITTING ROOM',     0.95), ('CASH WRAP',        0.95),
            ('TENANT SPACE',     0.85), ('RETAIL',           0.85),
            ('STOCK ROOM',       0.7),
            ('STOREFRONT',       0.35),
            ('DISPLAY',          0.4),
        ],
        'negative':  ['PATIENT ROOM', 'GUEST ROOM', 'FORKLIFT', 'LOADING DOCK'],
        'threshold': 1.20,  # HIGH — STOREFRONT is common false positive
    },

    'parking': {
        'keywords': [
            ('PARKING STALL',    1.0), ('CAR STALL',         1.0),
            ('DRIVE AISLE',      0.95), ('PARKING GARAGE',   1.0),
            ('PARKING STRUCTURE', 1.0),
            ('ACCESSIBLE STALL', 0.9), ('COMPACT STALL',     0.9),
            ('TYP. STALL',       0.9),
            ('RAMP',             0.7),
            ('PARKING',          0.55),
        ],
        'negative':  ['PATIENT ROOM', 'GUEST ROOM', 'LOADING DOCK', 'RACKING'],
        'threshold': 0.95,
    },

    'education': {
        'keywords': [
            ('CLASSROOM',        1.0), ('LECTURE HALL',      1.0),
            ('LABORATORY',       0.9), ('GYMNASIUM',         0.95),
            ('CAFETERIA',        0.85), ('AUDITORIUM',       0.9),
            ('FACULTY',          0.8), ('STUDENT',           0.7),
            ('LIBRARY',          0.75), ('LOCKER ROOM',      0.6),
        ],
        'negative':  ['GUEST ROOM', 'PATIENT ROOM', 'LOADING DOCK'],
        'threshold': 0.90,
    },
}

# Construction type keyword signals
CONSTRUCTION_KW = {
    'cmu':      ['CMU', 'CONCRETE MASONRY', 'MASONRY UNIT'],
    'pemb':     ['PEMB', 'PRE-ENGINEERED', 'METAL BUILDING'],
    'steel':    ['METAL STUD', 'STEEL STUD', 'MTL STUD'],
    'wood':     ['WOOD STUD', '2X4', '2X6'],
    'concrete': ['CONCRETE WALL', 'CAST-IN-PLACE', 'CIP CONCRETE', 'SHEAR WALL'],
}

TYPICAL_KW  = ['TYPICAL FLOOR', 'TYP. FLOOR', 'TYPICAL LEVEL', 'FLOORS 3-', 'LEVELS 3-']
PARKING_KW  = ['PARKING STALL', 'CAR STALL', 'DRIVE AISLE', 'PARKING GARAGE']
BASEMENT_KW = ['BASEMENT', 'BELOW GRADE', ' B1 ', ' B2 ']

SHEET_TITLES = {
    'FIRST FLOOR PLAN': 1,  'GROUND FLOOR PLAN': 1,
    'SECOND FLOOR PLAN': 2, 'THIRD FLOOR PLAN': 3,
    'FOURTH FLOOR PLAN': 4, 'FIFTH FLOOR PLAN': 5,
    'SIXTH FLOOR PLAN': 6,  'SEVENTH FLOOR PLAN': 7,
    'LEVEL 1 PLAN': 1,      'LEVEL 2 PLAN': 2,
    'LEVEL 3 PLAN': 3,      'LEVEL 4 PLAN': 4,
}


# ── BUILDING PROFILE ──────────────────────────────────────────────────────────

@dataclass
class BuildingProfile:
    page_count:        int
    floor_count:       int   = 1
    has_parking:       bool  = False
    has_basement:      bool  = False
    has_typical_floor: bool  = False
    is_high_rise:      bool  = False
    occupancy_type:    str   = 'unknown'
    occupancy_score:   float = 0.0
    construction:      List[str] = field(default_factory=list)
    engine_type:       str   = 'single_floor'
    confidence:        float = 0.0
    rf_params:         dict  = field(default_factory=dict)
    notes:             List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'page_count':        self.page_count,
            'floor_count':       self.floor_count,
            'has_parking':       self.has_parking,
            'has_basement':      self.has_basement,
            'has_typical_floor': self.has_typical_floor,
            'is_high_rise':      self.is_high_rise,
            'occupancy_type':    self.occupancy_type,
            'occupancy_score':   self.occupancy_score,
            'construction':      self.construction,
            'engine_type':       self.engine_type,
            'confidence':        self.confidence,
            'rf_params':         self.rf_params,
            'notes':             self.notes,
        }


# ── CLASSIFIER ────────────────────────────────────────────────────────────────

class BuildingClassifier:
    """
    Classify a building from its PDF text corpus.

    Usage:
        classifier = BuildingClassifier()
        profile = classifier.classify(corpus="...", page_count=10)
    """

    def classify(self, corpus: str, page_count: int) -> BuildingProfile:
        """corpus should be the full uppercased text of all pages joined."""
        corpus = corpus.upper()
        p = BuildingProfile(page_count=page_count)
        self._detect_floors(p, corpus, page_count)
        self._detect_occupancy(p, corpus)
        self._detect_construction(p, corpus)
        self._route(p)
        return p

    # ── FLOOR DETECTION ───────────────────────────────────────────────────────

    def _detect_floors(self, p: BuildingProfile, corpus: str, page_count: int) -> None:
        p.has_parking       = sum(1 for kw in PARKING_KW if kw in corpus) >= 2
        p.has_basement      = any(kw in corpus for kw in BASEMENT_KW)
        p.has_typical_floor = any(kw in corpus for kw in TYPICAL_KW)

        if page_count > 1:
            p.floor_count = page_count
            p.notes.append(f"Floors from page count: {page_count}")
        elif p.has_typical_floor:
            m = re.search(r'FLOORS?\s+\d+\s*[-]\s*(\d+)', corpus)
            p.floor_count = int(m.group(1)) if m else 8
            p.notes.append(f"Typical floor: {p.floor_count} floors")
        else:
            found = [v for k, v in SHEET_TITLES.items() if k in corpus]
            p.floor_count = max(found) if found else 1
            p.notes.append(f"Floor count: {p.floor_count}")

        p.is_high_rise = p.floor_count >= 7

    # ── WEIGHTED OCCUPANCY SCORING ────────────────────────────────────────────

    def _detect_occupancy(self, p: BuildingProfile, corpus: str) -> None:
        """
        Score each occupancy type using weighted keyword hits.
        A category must exceed its threshold AND have no negative hits.
        """
        scores: dict[str, float] = {}
        detail: dict[str, dict] = {}

        for occ, config in OCCUPANCY_WEIGHTED.items():
            blocked = [kw for kw in config['negative'] if kw in corpus]
            if blocked:
                scores[occ] = 0.0
                detail[occ] = {'score': 0.0, 'hits': [], 'blocked': blocked}
                continue

            hits = []
            total = 0.0
            for kw, weight in config['keywords']:
                if kw in corpus:
                    count = corpus.count(kw)
                    effective_weight = weight * min(1.0 + (count - 1) * 0.1, 1.5)
                    total += effective_weight
                    hits.append((kw, weight, count))

            scores[occ] = total
            detail[occ] = {
                'score': total,
                'hits': hits,
                'blocked': [],
                'threshold': config['threshold'],
                'passes': total >= config['threshold'],
            }

        passing = {occ: s for occ, s in scores.items()
                   if detail[occ].get('passes', False)}

        if passing:
            primary = max(passing, key=passing.get)
            p.occupancy_type  = primary
            p.occupancy_score = scores[primary]
        elif scores:
            primary = max(scores, key=scores.get)
            p.occupancy_type  = primary if scores[primary] > 0.1 else 'unknown'
            p.occupancy_score = scores[primary]
        else:
            p.occupancy_type  = 'unknown'
            p.occupancy_score = 0.0

        top3 = sorted(scores.items(), key=lambda x: -x[1])[:3]
        p.notes.append("Occupancy scores: " + ', '.join(f"{o}={s:.2f}" for o, s in top3))
        p.notes.append(f"Occupancy → {p.occupancy_type} ({p.occupancy_score:.2f})")

    # ── CONSTRUCTION TYPE ─────────────────────────────────────────────────────

    def _detect_construction(self, p: BuildingProfile, corpus: str) -> None:
        for ctype, kws in CONSTRUCTION_KW.items():
            if any(kw in corpus for kw in kws):
                p.construction.append(ctype)

    # ── ENGINE ROUTING ────────────────────────────────────────────────────────

    def _route(self, p: BuildingProfile) -> None:
        occ = p.occupancy_type

        if p.has_parking and occ == 'parking':
            p.engine_type = 'parking';     p.confidence = 0.90
        elif occ == 'healthcare':
            p.engine_type = 'healthcare';  p.confidence = 0.90
        elif p.is_high_rise or p.has_typical_floor:
            p.engine_type = 'high_rise';   p.confidence = 0.88
        elif p.floor_count > 1:
            p.engine_type = 'multi_floor'; p.confidence = 0.85
        else:
            p.engine_type = 'single_floor'; p.confidence = 0.95

        # Hotel RF override for multi/high-rise hotels
        rf_key = ('hotel'
                  if occ == 'hotel' and p.floor_count > 1
                  else p.engine_type)
        p.rf_params = ENGINE_RF.get(rf_key, ENGINE_RF['single_floor'])
        p.notes.append(f"→ {p.engine_type.upper()} ({p.confidence:.0%})")


# Singleton
classifier = BuildingClassifier()
