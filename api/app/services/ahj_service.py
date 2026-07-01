"""
services/ahj_service.py — AHJ lookup with PostgreSQL backing.

Lookup order:
  1. Exact jurisdiction match in DB (city-level entries seeded from AHJ_DB)
  2. Partial match in DB
  3. CA county fallback (constructed dynamically — not stored in DB)
  4. CA state default (constructed dynamically)
  5. Out-of-state default (constructed dynamically)

Seeding: call seed_ahj_records() at startup if the table is empty.
"""

import re
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ahj import AHJRecord

logger = logging.getLogger(__name__)


# ── AHJ PROFILE DATACLASS ─────────────────────────────────────────────────────

@dataclass
class AHJProfile:
    # Identity
    name:               str
    abbreviation:       str
    jurisdiction:       str
    state:              str
    website:            str   = ''

    # RF Requirements
    min_signal_dbm:     float = -95.0
    design_target_dbm:  float = -85.0
    coverage_pct:       float = 95.0
    critical_areas_pct: float = 99.0

    # Frequency bands
    freq_bands:         List[str] = field(default_factory=lambda: ['700MHz'])

    # Battery backup
    battery_hours:      float = 24.0

    # High-rise
    highrise_threshold_ft: float = 55.0
    highrise_coverage_pct: float = 99.0

    # Submittal flags
    requires_preliminary:       bool = True
    requires_construction_docs: bool = True
    requires_donor_path_study:  bool = False
    requires_third_party_test:  bool = False
    requires_facp_integration:  bool = True
    requires_signed_plans:      bool = True

    # Lists
    special_requirements: List[str] = field(default_factory=list)
    codes:                List[str] = field(default_factory=lambda: [
        'CFC §510', 'NFPA 1225-2022', 'IFC §915', 'FCC Part 90'
    ])

    # Internal
    confidence:  str = 'exact'
    matched_by:  str = ''

    def to_dict(self) -> dict:
        return {
            'name':                       self.name,
            'abbreviation':               self.abbreviation,
            'jurisdiction':               self.jurisdiction,
            'state':                      self.state,
            'website':                    self.website,
            'min_signal_dbm':             self.min_signal_dbm,
            'design_target_dbm':          self.design_target_dbm,
            'coverage_pct':               self.coverage_pct,
            'critical_areas_pct':         self.critical_areas_pct,
            'freq_bands':                 self.freq_bands,
            'battery_hours':              self.battery_hours,
            'highrise_threshold_ft':      self.highrise_threshold_ft,
            'highrise_coverage_pct':      self.highrise_coverage_pct,
            'requires_preliminary':       self.requires_preliminary,
            'requires_construction_docs': self.requires_construction_docs,
            'requires_donor_path_study':  self.requires_donor_path_study,
            'requires_third_party_test':  self.requires_third_party_test,
            'requires_facp_integration':  self.requires_facp_integration,
            'requires_signed_plans':      self.requires_signed_plans,
            'special_requirements':       self.special_requirements,
            'codes':                      self.codes,
            'confidence':                 self.confidence,
            'matched_by':                 self.matched_by,
        }


# ── HARDCODED DEFAULTS ────────────────────────────────────────────────────────

CA_DEFAULT = AHJProfile(
    name               = 'California State Fire Marshal (Default)',
    abbreviation       = 'OSFM',
    jurisdiction       = 'California',
    state              = 'CA',
    website            = 'https://osfm.fire.ca.gov',
    min_signal_dbm     = -95.0,
    design_target_dbm  = -85.0,
    coverage_pct       = 95.0,
    critical_areas_pct = 99.0,
    freq_bands         = ['700MHz'],
    battery_hours      = 24.0,
    highrise_threshold_ft = 55.0,
    highrise_coverage_pct = 99.0,
    codes              = ['CFC §510.1', 'NFPA 1225-2022', 'IFC §915'],
    special_requirements = [
        'Preliminary layout required prior to permit issuance',
        'BDA must be listed per UL 2524',
        'Dry contacts to FACP required per CFC §510.4.2.5',
    ],
    confidence = 'default',
    matched_by = 'state default',
)

OUT_OF_STATE_DEFAULT = AHJProfile(
    name               = 'Local AHJ (Non-California)',
    abbreviation       = 'LOCAL',
    jurisdiction       = 'Unknown',
    state              = 'XX',
    min_signal_dbm     = -95.0,
    design_target_dbm  = -85.0,
    coverage_pct       = 95.0,
    critical_areas_pct = 99.0,
    freq_bands         = ['700MHz'],
    battery_hours      = 12.0,
    codes              = ['IFC §915', 'NFPA 1225-2022', 'FCC Part 90'],
    special_requirements = [
        'Verify local AHJ requirements — non-California jurisdiction',
        'IFC §915 applies as baseline',
    ],
    confidence = 'default',
    matched_by = 'out-of-state default',
)

CA_COUNTY_AHJ = {
    'ALAMEDA':        'Alameda County Fire Department',
    'CONTRA COSTA':   'Contra Costa County Fire Protection District',
    'SANTA CLARA':    'Santa Clara County Fire Department',
    'SAN MATEO':      'San Mateo County Fire Department',
    'MARIN':          'Marin County Fire',
    'SONOMA':         'Sonoma County Fire & Emergency Services',
    'ORANGE':         'Orange County Fire Authority (OCFA)',
    'RIVERSIDE':      'Riverside County Fire Department (CAL FIRE)',
    'SAN BERNARDINO': 'San Bernardino County Fire Department',
    'LOS ANGELES':    'Los Angeles County Fire Department',
    'SAN DIEGO':      'San Diego County Fire Authority',
    'SACRAMENTO':     'Sacramento Metropolitan Fire District',
    'FRESNO':         'Fresno County Fire Protection District',
    'KERN':           'Kern County Fire Department',
    'VENTURA':        'Ventura County Fire Department',
}

# Seed data — mirroring the partner's AHJ_DB dict
# Each entry maps to AHJRecord field values
AHJ_SEED_DATA: list[dict] = [
    dict(
        name='San Francisco Fire Department', abbreviation='SFFD',
        jurisdiction='San Francisco', state='CA',
        website='https://sf.gov/departments/fire-department',
        min_signal_dbm=-95.0, design_target_dbm=-85.0,
        coverage_pct=95.0, critical_areas_pct=99.0,
        freq_bands=['700MHz', '800MHz'],
        battery_hours=24.0,
        highrise_threshold_ft=55.0, highrise_coverage_pct=99.0,
        requires_donor_path_study=True,
        special_requirements=[
            'SFFD requires 700 MHz AND 800 MHz P25 Phase II coverage',
            'Must submit to SFFD Bureau of Fire Prevention for pre-approval',
            'Donor antenna location must be approved by SFFD',
            'SFFD-approved testing protocol required at acceptance',
            'Critical areas (stairs, elevators, exits): 99% minimum',
        ],
        codes=['CFC §510', 'SFFD Admin Code §38', 'NFPA 1225-2022'],
        confidence='exact',
    ),
    dict(
        name='Los Angeles Fire Department', abbreviation='LAFD',
        jurisdiction='Los Angeles', state='CA',
        website='https://lafd.org',
        min_signal_dbm=-95.0, design_target_dbm=-85.0,
        coverage_pct=95.0, critical_areas_pct=99.0,
        freq_bands=['700MHz'],
        battery_hours=24.0,
        highrise_threshold_ft=75.0, highrise_coverage_pct=99.0,
        requires_donor_path_study=False,
        special_requirements=[
            'LAFD ERRCS Advisory Board review required for all new systems',
            'Submit to LAFD Bureau of Engineering for pre-approval',
            'LAFD approved contractor list required',
            'High-rise: 99% coverage required at -95 dBm',
            'Bi-annual testing required after acceptance',
        ],
        codes=['CFC §510', 'LAMC §57.119.3.2', 'NFPA 1225-2022'],
        confidence='exact',
    ),
    dict(
        name='San Jose Fire Department', abbreviation='SJFD',
        jurisdiction='San Jose', state='CA',
        website='https://www.sanjoseca.gov/your-government/departments/fire',
        min_signal_dbm=-95.0, design_target_dbm=-85.0,
        coverage_pct=95.0, critical_areas_pct=99.0,
        freq_bands=['700MHz'],
        battery_hours=24.0,
        special_requirements=[
            'SJFD pre-submittal meeting recommended for buildings > 50,000 SF',
            'Acceptance test must be witnessed by SJFD inspector',
        ],
        codes=['CFC §510', 'SJMC Title 16', 'NFPA 1225-2022'],
        confidence='exact',
    ),
    dict(
        name='Oakland Fire Department', abbreviation='OFD',
        jurisdiction='Oakland', state='CA',
        website='https://www.oaklandca.gov/departments/fire',
        min_signal_dbm=-95.0, design_target_dbm=-85.0,
        coverage_pct=95.0, critical_areas_pct=99.0,
        freq_bands=['700MHz'],
        battery_hours=24.0,
        requires_donor_path_study=True,
        special_requirements=[
            'OFD requires donor path propagation analysis with submittal',
            'Walk test protocol: 3-ft grid in all areas',
            'Stairwells and elevator cabs: 100% coverage required',
        ],
        codes=['CFC §510', 'OMC §15.12', 'NFPA 1225-2022'],
        confidence='exact',
    ),
    dict(
        name='Sacramento Fire Department', abbreviation='SACFD',
        jurisdiction='Sacramento', state='CA',
        website='https://www.cityofsacramento.org/Fire',
        min_signal_dbm=-95.0, design_target_dbm=-85.0,
        coverage_pct=95.0, critical_areas_pct=99.0,
        freq_bands=['700MHz'],
        battery_hours=24.0,
        requires_donor_path_study=True,
        special_requirements=[
            'Sacramento requires propagation study showing donor signal path',
            'Submit to Sacramento Metro Fire District if outside city limits',
        ],
        codes=['CFC §510', 'SMC §15.56', 'NFPA 1225-2022'],
        confidence='exact',
    ),
    dict(
        name='San Diego Fire-Rescue Department', abbreviation='SDFD',
        jurisdiction='San Diego', state='CA',
        website='https://www.sandiego.gov/fire',
        min_signal_dbm=-95.0, design_target_dbm=-85.0,
        coverage_pct=95.0, critical_areas_pct=99.0,
        freq_bands=['700MHz'],
        battery_hours=24.0,
        special_requirements=[
            'SDFD ERRCS review required via SDFD Prevention Bureau',
        ],
        codes=['CFC §510', 'SDMC §91.0508.9', 'NFPA 1225-2022'],
        confidence='exact',
    ),
    dict(
        name='Fremont Fire Department', abbreviation='FFD',
        jurisdiction='Fremont', state='CA',
        freq_bands=['700MHz'], battery_hours=24.0,
        codes=['CFC §510', 'NFPA 1225-2022'],
        confidence='exact',
    ),
    dict(
        name='Long Beach Fire Department', abbreviation='LBFD',
        jurisdiction='Long Beach', state='CA',
        freq_bands=['700MHz'], battery_hours=24.0,
        codes=['CFC §510', 'NFPA 1225-2022'],
        confidence='exact',
    ),
    dict(
        name='Anaheim Fire & Rescue', abbreviation='AFR',
        jurisdiction='Anaheim', state='CA',
        freq_bands=['700MHz'], battery_hours=24.0,
        codes=['CFC §510', 'NFPA 1225-2022'],
        confidence='exact',
    ),
    dict(
        name='Santa Ana Fire Department', abbreviation='SAFD',
        jurisdiction='Santa Ana', state='CA',
        freq_bands=['700MHz'], battery_hours=24.0,
        codes=['CFC §510', 'NFPA 1225-2022'],
        confidence='exact',
    ),
    dict(
        name='Mountain View Fire Department / Santa Clara County Fire',
        abbreviation='MVFD',
        jurisdiction='Mountain View', state='CA',
        freq_bands=['700MHz'], battery_hours=24.0,
        codes=['CFC §510', 'NFPA 1225-2022'],
        confidence='exact',
    ),
    dict(
        name='Pleasanton Fire Department / Alameda County Fire',
        abbreviation='PFD',
        jurisdiction='Pleasanton', state='CA',
        freq_bands=['700MHz'], battery_hours=24.0,
        codes=['CFC §510', 'NFPA 1225-2022'],
        confidence='exact',
    ),
    dict(
        name='Berkeley Fire Department', abbreviation='BFD',
        jurisdiction='Berkeley', state='CA',
        freq_bands=['700MHz'], battery_hours=24.0,
        codes=['CFC §510', 'BMC §19.28', 'NFPA 1225-2022'],
        confidence='exact',
    ),
    dict(
        name='Riverside Fire Department / Riverside County Fire',
        abbreviation='RFD',
        jurisdiction='Riverside', state='CA',
        freq_bands=['700MHz'], battery_hours=24.0,
        codes=['CFC §510', 'NFPA 1225-2022'],
        confidence='exact',
    ),
    dict(
        name='Irvine Fire Department / Orange County Fire Authority',
        abbreviation='OCFA',
        jurisdiction='Irvine', state='CA',
        freq_bands=['700MHz'], battery_hours=24.0,
        special_requirements=[
            'Orange County Fire Authority may have jurisdiction in unincorporated areas',
        ],
        codes=['CFC §510', 'NFPA 1225-2022'],
        confidence='exact',
    ),
    # Out-of-state
    dict(
        name='Austin Fire Department', abbreviation='AFD',
        jurisdiction='Austin', state='TX',
        freq_bands=['700MHz'], battery_hours=12.0,
        codes=['IFC §915', 'NFPA 1225-2022', 'Austin Fire Code §915'],
        special_requirements=['Verify current Austin amendments to IFC §915'],
        confidence='exact',
    ),
    dict(
        name='Hutto Fire Department / Williamson County', abbreviation='HFD',
        jurisdiction='Hutto', state='TX',
        freq_bands=['700MHz'], battery_hours=12.0,
        codes=['IFC §915', 'NFPA 1225-2022'],
        special_requirements=[
            'Small jurisdiction — verify requirements with Hutto Building Dept',
            'Williamson County Emergency Services District may have jurisdiction',
        ],
        confidence='exact',
    ),
    dict(
        name='FDNY (Fire Department City of New York)', abbreviation='FDNY',
        jurisdiction='New York', state='NY',
        freq_bands=['700MHz', '800MHz'],
        battery_hours=24.0,
        requires_donor_path_study=True,
        requires_third_party_test=True,
        special_requirements=[
            'FDNY COF (Certificate of Fitness) required for installer',
            'FDNY approval required before any antenna installation',
            'NYC Fire Code §907.2.24 and FC 917',
        ],
        codes=['NYC FC §917', 'NFPA 1225-2022'],
        confidence='exact',
    ),
    dict(
        name='Chicago Fire Department', abbreviation='CFD',
        jurisdiction='Chicago', state='IL',
        freq_bands=['700MHz'], battery_hours=24.0,
        codes=['Chicago MCC §13-196-205', 'IFC §915', 'NFPA 1225-2022'],
        confidence='exact',
    ),
]


# ── ADDRESS PARSER ────────────────────────────────────────────────────────────

def parse_address(address_string: str) -> dict:
    """Extract city, state, ZIP from an address string."""
    addr = address_string.upper().strip()
    result: dict = {'raw': address_string, 'street': None, 'city': None,
                    'state': None, 'zip': None}

    m = re.search(r'\b(\d{5})(?:-\d{4})?\b', addr)
    if m:
        result['zip'] = m.group(1)

    m = re.search(r'\b([A-Z]{2})\s+\d{5}', addr)
    if m:
        result['state'] = m.group(1)

    m = re.search(r',\s*([A-Z][A-Z\s\.]+?)\s*,?\s*[A-Z]{2}\s+\d{5}', addr)
    if m:
        result['city'] = m.group(1).strip().rstrip(',').strip()
    else:
        parts = [p.strip() for p in re.split(r'[,\n]', addr) if p.strip()]
        for part in reversed(parts):
            if re.search(r'[A-Z]{2}\s+\d{5}', part):
                city_part = re.sub(r'\s*[A-Z]{2}\s+\d{5}.*', '', part).strip()
                if city_part and not re.match(r'^\d', city_part):
                    result['city'] = city_part
                break
            elif part and not re.match(r'^\d', part):
                result['city'] = part
                break

    if result['city']:
        result['city'] = re.sub(r'\s+', ' ', result['city']).strip()

    return result


def _record_to_profile(record: AHJRecord, matched_by: str) -> AHJProfile:
    """Convert an ORM AHJRecord row to an AHJProfile dataclass."""
    return AHJProfile(
        name=record.name,
        abbreviation=record.abbreviation,
        jurisdiction=record.jurisdiction,
        state=record.state,
        website=record.website or '',
        min_signal_dbm=float(record.min_signal_dbm),
        design_target_dbm=float(record.design_target_dbm),
        coverage_pct=float(record.coverage_pct),
        critical_areas_pct=float(record.critical_areas_pct),
        freq_bands=list(record.freq_bands or ['700MHz']),
        battery_hours=float(record.battery_hours),
        highrise_threshold_ft=float(record.highrise_threshold_ft),
        highrise_coverage_pct=float(record.highrise_coverage_pct),
        requires_preliminary=record.requires_preliminary,
        requires_construction_docs=record.requires_construction_docs,
        requires_donor_path_study=record.requires_donor_path_study,
        requires_third_party_test=record.requires_third_party_test,
        requires_facp_integration=record.requires_facp_integration,
        requires_signed_plans=record.requires_signed_plans,
        special_requirements=list(record.special_requirements or []),
        codes=list(record.codes or []),
        confidence=record.confidence,
        matched_by=matched_by,
    )


# ── LOOKUP ────────────────────────────────────────────────────────────────────

async def lookup_ahj(address: str, session: AsyncSession) -> AHJProfile:
    """
    DB-backed AHJ lookup. Falls back to hardcoded CA/out-of-state defaults.
    """
    parsed = parse_address(address)
    city   = (parsed.get('city') or '').upper().strip()
    state  = (parsed.get('state') or '').upper().strip()

    # 1. Exact jurisdiction match in DB
    if city:
        result = await session.execute(
            select(AHJRecord).where(
                func.upper(AHJRecord.jurisdiction) == city
            )
        )
        record = result.scalar_one_or_none()
        if record:
            return _record_to_profile(record, matched_by=f"city: {city}")

    # 2. Partial match — DB jurisdiction is substring of city or vice versa
    if city:
        result = await session.execute(select(AHJRecord))
        all_records = result.scalars().all()
        for record in all_records:
            db_jur = record.jurisdiction.upper()
            if db_jur in city or city in db_jur:
                return _record_to_profile(
                    record, matched_by=f"partial city: {city} → {record.jurisdiction}"
                )

    # 3. CA county fallback (dynamic — not stored in DB)
    if state == 'CA':
        for county, ahj_name in CA_COUNTY_AHJ.items():
            if county in city or county in address.upper():
                return AHJProfile(
                    name=ahj_name,
                    abbreviation=ahj_name.split()[0],
                    jurisdiction=f'{county.title()} County',
                    state='CA',
                    min_signal_dbm=-95.0,
                    coverage_pct=95.0,
                    freq_bands=['700MHz'],
                    battery_hours=24.0,
                    codes=['CFC §510', 'NFPA 1225-2022'],
                    confidence='county',
                    matched_by=f"county: {county}",
                    special_requirements=[
                        f'Unincorporated area — verify with {ahj_name}',
                        'Confirm jurisdiction boundaries before submittal',
                    ],
                )

        # 4. CA state default
        profile = AHJProfile(**CA_DEFAULT.__dict__.copy())
        profile.matched_by = f"CA default (city '{city}' not in database)"
        return profile

    # 5. Out-of-state default
    profile = AHJProfile(**OUT_OF_STATE_DEFAULT.__dict__.copy())
    profile.jurisdiction = city or 'Unknown'
    profile.state        = state or 'XX'
    profile.matched_by   = f"out-of-state default ({state})"
    return profile


# ── SEEDING ───────────────────────────────────────────────────────────────────

async def seed_ahj_records(session: AsyncSession) -> None:
    """
    Insert all AHJ_SEED_DATA into ahj_records if the table is empty.
    Safe to call on every startup — no-ops if data already exists.
    """
    count_result = await session.execute(select(func.count()).select_from(AHJRecord))
    count = count_result.scalar_one()
    if count > 0:
        logger.info("AHJ table already seeded (%d records), skipping.", count)
        return

    defaults = {
        'min_signal_dbm':             -95.0,
        'design_target_dbm':          -85.0,
        'coverage_pct':               95.0,
        'critical_areas_pct':         99.0,
        'freq_bands':                 ['700MHz'],
        'battery_hours':              24.0,
        'highrise_threshold_ft':      55.0,
        'highrise_coverage_pct':      99.0,
        'requires_preliminary':       True,
        'requires_construction_docs': True,
        'requires_donor_path_study':  False,
        'requires_third_party_test':  False,
        'requires_facp_integration':  True,
        'requires_signed_plans':      True,
        'special_requirements':       [],
        'codes':                      ['CFC §510', 'NFPA 1225-2022', 'IFC §915', 'FCC Part 90'],
        'website':                    '',
        'confidence':                 'exact',
    }

    records = []
    for data in AHJ_SEED_DATA:
        merged = {**defaults, **data}
        records.append(AHJRecord(**merged))

    session.add_all(records)
    await session.commit()
    logger.info("Seeded %d AHJ records.", len(records))
