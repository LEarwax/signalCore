"""
pdf_service.py — PDF upload processing.

Per-page pipeline:
  1. Decode text with CID-font correction (ported from partner's geometry.py)
  2. Classify sheet type from keyword patterns
  3. Extract sheet label from title block area
  4. Store raw PDF in storage (S3 or local)
  5. Persist PDFUpload + Sheet rows to DB

Thumbnails are intentionally skipped at upload time (null → gray placeholder
in UI). They will be generated per-selected-sheet at engine run time (SIG-3).
"""

import io
import re
import uuid
import logging
from collections import defaultdict
from typing import List, Tuple

import pdfplumber
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.upload import PDFUpload, Sheet
from app.services.storage_service import storage

logger = logging.getLogger(__name__)


# ── CID FONT DECODE (ported from core/geometry.py) ───────────────────────────

def _detect_cid_offset(chars: list) -> int:
    """Auto-detect CID→ASCII encoding offset (typically 29 for Arial subsets)."""
    best, score = 29, 0
    for offset in range(0, 50):
        s = sum(
            1 for c in chars[:500]
            if "(cid:" in c.get("text", "")
            and 32 <= (int(c["text"].split(":")[1].rstrip(")")) + offset) <= 122
        )
        if s > score:
            score, best = s, offset
    return best


def _decode_page_text(page) -> Tuple[list, str]:
    """
    Decode all characters on a pdfplumber page into row-grouped lines.
    Returns (rows, corpus) where rows = [(top, x0, text), ...] and corpus is
    the full uppercased text joined into one string.
    """
    chars = page.chars
    offset = _detect_cid_offset(chars)
    row_map: dict = defaultdict(list)
    for c in chars:
        row_map[round(c["top"] / 2) * 2].append(c)

    rows = []
    for top_key in sorted(row_map.keys()):
        row = sorted(row_map[top_key], key=lambda x: x["x0"])
        decoded = ""
        xs = []
        for c in row:
            txt = c.get("text", "")
            xs.append(c["x0"])
            if "(cid:" in txt:
                try:
                    cid = int(txt.split(":")[1].rstrip(")"))
                    decoded += chr(cid + offset) if 32 <= cid + offset <= 126 else "."
                except Exception:
                    decoded += "."
            elif txt:
                decoded += txt[0]
        if decoded.strip():
            rows.append((top_key, min(xs) if xs else 0, decoded.strip()))

    corpus = " ".join(t for _, _, t in rows).upper()
    return rows, corpus


# ── SHEET TYPE CLASSIFICATION ─────────────────────────────────────────────────

_FLOOR_PLAN_KW = re.compile(
    r"\b(FLOOR\s+PLAN|LEVEL\s+\d+\s+PLAN|FIRST\s+FLOOR|SECOND\s+FLOOR|"
    r"THIRD\s+FLOOR|FOURTH\s+FLOOR|FIFTH\s+FLOOR|GROUND\s+FLOOR|"
    r"BASEMENT\s+PLAN|ROOF\s+PLAN|MEZZANINE\s+PLAN|PARKING\s+PLAN|"
    r"LEVEL\s+\d+|FLOOR\s+\d+)\b"
)
_ELEVATION_KW = re.compile(r"\b(ELEVATION|ELEV\.?)\b")
_SECTION_KW   = re.compile(r"\b(SECTION|SECT\.?|BUILDING\s+SECTION|WALL\s+SECTION)\b")
_DETAIL_KW    = re.compile(r"\b(DETAIL|DTL\.?|TYP\.\s+DETAIL)\b")


def _classify_sheet_type(corpus: str) -> str:
    if _FLOOR_PLAN_KW.search(corpus):
        return "floor_plan"
    if _ELEVATION_KW.search(corpus):
        return "elevation"
    if _SECTION_KW.search(corpus):
        return "section"
    if _DETAIL_KW.search(corpus):
        return "detail"
    return "other"


# ── SHEET LABEL EXTRACTION ────────────────────────────────────────────────────

# Sheet number patterns: A-101, A101, FP-1, S-200, E-001, etc.
_SHEET_NUM_PAT = re.compile(r"\b([A-Z]{1,3}-?\d{2,4}[a-zA-Z]?)\b")

# Friendly title phrases in order of preference
_TITLE_PHRASES = [
    "FLOOR PLAN", "FIRST FLOOR", "SECOND FLOOR", "THIRD FLOOR", "FOURTH FLOOR",
    "FIFTH FLOOR", "SIXTH FLOOR", "SEVENTH FLOOR", "GROUND FLOOR", "BASEMENT PLAN",
    "ROOF PLAN", "MEZZANINE", "PARKING PLAN", "LEVEL", "ELEVATION", "SECTION",
    "DETAIL", "SITE PLAN", "COVER SHEET",
]


def _extract_label(rows: list, page_width: float, page_height: float, page_num: int) -> str:
    """
    Extract sheet number + title from title block zone (right 30%, lower 70%).
    Falls back to first found sheet number or 'Page N'.
    """
    tb_x = page_width * 0.70
    tb_y = page_height * 0.25

    # Title block rows
    tb_rows = [(top, x0, txt.upper().strip()) for top, x0, txt in rows
               if x0 > tb_x and top > tb_y]

    tb_text = " ".join(t for _, _, t in tb_rows)

    # Find sheet number
    sheet_num: str | None = None
    m = _SHEET_NUM_PAT.search(tb_text)
    if m:
        sheet_num = m.group(1).upper()
    else:
        # Also try anywhere on the page
        full_text = " ".join(t for _, _, t in rows)
        m2 = _SHEET_NUM_PAT.search(full_text)
        if m2:
            sheet_num = m2.group(1).upper()

    # Find title phrase
    title: str | None = None
    for phrase in _TITLE_PHRASES:
        if phrase in tb_text:
            title = phrase.title()
            break

    if sheet_num and title:
        return f"{sheet_num} — {title}"
    if sheet_num:
        return sheet_num
    if title:
        return title
    return f"Page {page_num}"


# ── MAIN PROCESSING FUNCTION ──────────────────────────────────────────────────

async def process_upload(
    session: AsyncSession,
    project_id: uuid.UUID,
    engineer_id: uuid.UUID,
    filename: str,
    file_bytes: bytes,
) -> PDFUpload:
    """
    Full upload pipeline:
      1. Store raw PDF in storage
      2. Open with pdfplumber, decode text per page
      3. Classify + label each sheet
      4. Persist PDFUpload + Sheet rows
      5. Return the PDFUpload ORM object (with .sheets loaded)
    """
    upload_id = uuid.uuid4()
    safe_name = re.sub(r"[^\w\-.]", "_", filename)
    pdf_key = f"uploads/{project_id}/{upload_id}/{safe_name}"

    # Store the raw PDF
    try:
        storage.upload(pdf_key, file_bytes, content_type="application/pdf")
        logger.info("Stored PDF at %s", pdf_key)
    except Exception as exc:
        logger.error("Storage upload failed: %s", exc)
        pdf_key = None  # non-fatal — continue with extraction

    # Extract sheets
    sheets: List[Sheet] = []
    page_count = 0

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            page_count = len(pdf.pages)
            for i, page in enumerate(pdf.pages, start=1):
                try:
                    rows, corpus = _decode_page_text(page)
                    sheet_type = _classify_sheet_type(corpus)
                    label = _extract_label(rows, page.width, page.height, i)
                except Exception as page_exc:
                    logger.warning("Page %d decode error: %s", i, page_exc)
                    sheet_type = "other"
                    label = f"Page {i}"

                sheets.append(Sheet(
                    upload_id=upload_id,
                    page_number=i,
                    label=label,
                    sheet_type=sheet_type,
                    thumbnail_url=None,  # generated at engine run time
                ))
    except Exception as exc:
        logger.error("pdfplumber failed: %s", exc)
        # Return a failed upload with zero sheets rather than crashing
        page_count = 0

    # Persist to DB
    db_upload = PDFUpload(
        id=upload_id,
        project_id=project_id,
        engineer_id=engineer_id,
        filename=filename,
        s3_key=pdf_key,
        page_count=page_count,
        status="ready" if sheets else "failed",
    )
    db_upload.sheets = sheets
    session.add(db_upload)
    await session.commit()
    await session.refresh(db_upload)

    # Eagerly load sheets (avoid lazy-load after session close)
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    result = await session.execute(
        select(PDFUpload)
        .options(selectinload(PDFUpload.sheets))
        .where(PDFUpload.id == upload_id)
    )
    return result.scalar_one()
