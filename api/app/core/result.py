"""
result.py — Result[T] discriminated union for service layer.
Services return Result instead of raising exceptions for flow control.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Generic, TypeVar
from fastapi import HTTPException
from fastapi.responses import JSONResponse

T = TypeVar("T")


@dataclass
class Result(Generic[T]):
    _value: T | None = field(default=None, repr=False)
    _error: str | list[str] | None = field(default=None, repr=False)
    _status: str = field(default="ok", repr=True)

    # ── factories ──────────────────────────────────────────────────

    @classmethod
    def ok(cls, value: T) -> "Result[T]":
        r: Result[T] = cls()
        r._value = value
        r._status = "ok"
        return r

    @classmethod
    def not_found(cls, message: str) -> "Result":
        r = cls()
        r._error = message
        r._status = "not_found"
        return r

    @classmethod
    def validation_error(cls, errors: str | list[str]) -> "Result":
        r = cls()
        r._error = errors
        r._status = "validation_error"
        return r

    @classmethod
    def failure(cls, message: str) -> "Result":
        r = cls()
        r._error = message
        r._status = "failure"
        return r

    @classmethod
    def forbidden(cls, message: str = "Forbidden") -> "Result":
        r = cls()
        r._error = message
        r._status = "forbidden"
        return r

    @classmethod
    def conflict(cls, message: str) -> "Result":
        r = cls()
        r._error = message
        r._status = "conflict"
        return r

    # ── accessors ──────────────────────────────────────────────────

    @property
    def is_ok(self) -> bool:
        return self._status == "ok"

    @property
    def value(self) -> T:
        if not self.is_ok:
            raise ValueError(f"Result is not ok: {self._error}")
        return self._value  # type: ignore

    # ── HTTP mapping ───────────────────────────────────────────────

    def to_response(self, status_code: int = 200):
        """Convert to FastAPI response. Raises HTTPException on error."""
        if self._status == "ok":
            return self._value
        elif self._status == "not_found":
            raise HTTPException(status_code=404, detail=self._error)
        elif self._status == "validation_error":
            raise HTTPException(status_code=422, detail=self._error)
        elif self._status == "forbidden":
            raise HTTPException(status_code=403, detail=self._error)
        elif self._status == "conflict":
            raise HTTPException(status_code=409, detail=self._error)
        else:
            raise HTTPException(status_code=500, detail=self._error or "Internal server error")
