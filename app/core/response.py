from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, Any

T = TypeVar('T')

class APIResponse(BaseModel, Generic[T]):
    status: bool
    code: int
    message: str
    data: Optional[T] = None