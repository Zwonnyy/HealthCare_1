import math
from dataclasses import dataclass
from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int

    @classmethod
    def create(cls, items: list[T], total: int, page: int, size: int) -> "PaginatedResponse[T]":
        return cls(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=math.ceil(total / size) if total > 0 else 1,
        )


@dataclass
class PaginationParams:
    page: int = Query(default=1, ge=1, description="페이지 번호 (1부터 시작)")
    size: int = Query(default=20, ge=1, le=100, description="페이지당 항목 수")

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size
