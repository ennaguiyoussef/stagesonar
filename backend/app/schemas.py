"""Modèles Pydantic : ce que l'API reçoit et renvoie."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, field_validator


class OfferOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    company: str
    location: str
    url: str
    published_at: datetime | None
    first_seen_at: datetime


class SubscriberCreate(BaseModel):
    email: EmailStr
    keywords: str
    location: str = ""

    @field_validator("keywords")
    @classmethod
    def keywords_must_not_be_empty(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Les mots-clés ne peuvent pas être vides.")

        return value


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    base_url: str
    is_active: bool
    last_run_at: datetime | None
