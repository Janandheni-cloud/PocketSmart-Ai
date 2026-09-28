"""
Pydantic request models used for validating incoming JSON bodies.
"""
from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    email: str = Field(min_length=5, max_length=160)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    email: str
    password: str


class HomeRequest(BaseModel):
    budget: float = Field(gt=0, le=10_000_000)
    room: str = Field(min_length=2, max_length=80)
    style: str = Field(min_length=2, max_length=80)
    items: str = Field(min_length=2, max_length=500)


class PartyRequest(BaseModel):
    budget: float = Field(gt=0, le=10_000_000)
    guests: int = Field(gt=0, le=10_000)
    event_type: str = Field(min_length=2, max_length=80)
    venue: str = Field(min_length=2, max_length=120)
    preferences: str = Field(default="", max_length=500)
