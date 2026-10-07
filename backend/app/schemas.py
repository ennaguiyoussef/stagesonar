"""Modèles Pydantic : ce que l'API reçoit et renvoie."""
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


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


class SourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    base_url: str
    is_active: bool
    last_run_at: datetime | None
