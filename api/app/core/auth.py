"""
auth.py — Auth0 JWT verification + Engineer auto-provisioning.
"""
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
import httpx

from app.core.config import settings
from app.core.database import get_db
from app.models.engineer import Engineer

bearer_scheme = HTTPBearer()

_jwks_cache: dict | None = None


async def _get_jwks() -> dict:
    global _jwks_cache
    if _jwks_cache is None:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://{settings.AUTH0_DOMAIN}/.well-known/jwks.json")
            _jwks_cache = resp.json()
    return _jwks_cache


async def verify_token(credentials: HTTPAuthorizationCredentials = Security(bearer_scheme)) -> dict:
    token = credentials.credentials
    try:
        jwks = await _get_jwks()
        payload = jwt.decode(
            token,
            jwks,
            algorithms=["RS256"],
            audience=settings.AUTH0_AUDIENCE,
            issuer=f"https://{settings.AUTH0_DOMAIN}/",
        )
        return payload
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


async def get_current_engineer(
    payload: dict = Depends(verify_token),
    db: AsyncSession = Depends(get_db),
) -> Engineer:
    """Resolve Auth0 sub → Engineer row, auto-provisioning on first request."""
    from sqlalchemy import select
    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Missing sub claim")

    result = await db.execute(select(Engineer).where(Engineer.auth0_sub == sub))
    engineer = result.scalar_one_or_none()

    if engineer is None:
        engineer = Engineer(
            auth0_sub=sub,
            email=payload.get("email", ""),
            name=payload.get("name", ""),
        )
        db.add(engineer)
        await db.commit()
        await db.refresh(engineer)

    return engineer
