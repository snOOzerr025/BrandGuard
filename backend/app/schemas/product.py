"""Pydantic request/response schemas for Products."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    description: Optional[str] = None
    source: str = "csv_upload"


class ProductRead(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    description: Optional[str]
    source: str
    created_at: datetime

    model_config = {"from_attributes": True}
