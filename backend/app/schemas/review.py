"""Pydantic request/response schemas for Reviews."""
import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator


class ReviewBase(BaseModel):
    title: Optional[str] = None
    text: str
    rating: Optional[int] = None
    source: str = "csv_upload"
    sentiment_label: Optional[str] = None

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 5):
            raise ValueError("Rating must be between 1 and 5")
        return v

    @field_validator("sentiment_label")
    @classmethod
    def validate_sentiment(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in {"positive", "negative", "neutral"}:
            raise ValueError("sentiment_label must be positive, negative, or neutral")
        return v


class ReviewCreate(ReviewBase):
    product_id: uuid.UUID


class ReviewRead(ReviewBase):
    id: uuid.UUID
    user_id: uuid.UUID
    product_id: uuid.UUID
    ingested_at: datetime

    model_config = {"from_attributes": True}


class ReviewIngest(BaseModel):
    """Schema for validating a single CSV row before DB insert."""
    name: str           # product name from CSV column " name"
    title: Optional[str] = None
    text: str
    rating: Optional[int] = None
    sentiment_label: Optional[str] = None

    @field_validator("text")
    @classmethod
    def text_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Review text cannot be empty")
        return v

    @field_validator("rating")
    @classmethod
    def validate_rating(cls, v: Optional[int]) -> Optional[int]:
        if v is not None and not (1 <= v <= 5):
            raise ValueError("Rating must be between 1 and 5")
        return v

    @field_validator("sentiment_label")
    @classmethod
    def validate_sentiment(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip() not in {"positive", "negative", "neutral"}:
            raise ValueError("sentiment_label must be positive, negative, or neutral")
        return v.strip() if v else v
