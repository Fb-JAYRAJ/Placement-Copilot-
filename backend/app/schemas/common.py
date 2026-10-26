from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None

class ErrorEnvelope(BaseModel):
    error: ErrorDetail

class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int
