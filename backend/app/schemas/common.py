from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Any | None = None

class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int

    @classmethod
    def from_items(
        cls,
        items: list[T],
        total: int | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> "PaginatedResponse[T]":
        tot = len(items) if total is None else total
        lim = len(items) if limit is None else limit
        return cls(items=items, total=tot, limit=lim, offset=offset)
