#Reusable types  (Pagination, health)

from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar("T")

class MessagePayload(BaseModel):
    message: str

class PaginatedResposne(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int

