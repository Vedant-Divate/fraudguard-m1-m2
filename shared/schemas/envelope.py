from datetime import datetime
from typing import Any, Generic, Optional, TypeVar
from pydantic import BaseModel
from enum import Enum

class StatusEnum(str, Enum):
    SUCCESS = "success"
    ERROR = "error"

class ErrorDetail(BaseModel):
    code: str
    message: str

class EnvelopeBase(BaseModel):
    request_id: str
    timestamp: datetime
    schema_version: str = "1.0"

class EnvelopeRequest(EnvelopeBase):
    data: dict[str, Any] | None = None

T = TypeVar('T')

class EnvelopeResponse(EnvelopeBase, Generic[T]):
    status: StatusEnum = StatusEnum.SUCCESS
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None