from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import date, datetime


# Auth
class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    name: str


class UserMe(BaseModel):
    user_id: int
    email: str
    name: str
    is_superuser: bool = False
    weekly_goal: Optional[int] = None
    monthly_goal: Optional[int] = None

    class Config:
        from_attributes = True


# Activities
class ActivityCreate(BaseModel):
    activity_type: str
    duration_minutes: Optional[float] = None
    distance_km: Optional[float] = None
    manual_steps: Optional[int] = None
    date: date
    notes: Optional[str] = None


class ActivityUpdate(BaseModel):
    activity_type: Optional[str] = None
    duration_minutes: Optional[float] = None
    distance_km: Optional[float] = None
    manual_steps: Optional[int] = None
    notes: Optional[str] = None


class ActivityResponse(BaseModel):
    id: int
    user_id: int
    activity_type: str
    duration_minutes: Optional[float] = None
    distance_km: Optional[float] = None
    manual_steps: Optional[int] = None
    step_equivalent_calculated: int
    date: date
    notes: Optional[str] = None
    source: str
    garmin_activity_id: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Leaderboards
class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    name: str
    total_steps: int
    goal: Optional[int] = None
    goal_progress: Optional[float] = None


# Settings
class ConversionRuleResponse(BaseModel):
    activity_type: str
    conversion_per_minute: float
    conversion_per_km: float
    step_multiplier: float = 1.0

    class Config:
        from_attributes = True


class ConversionRuleCreate(BaseModel):
    activity_type: str
    conversion_per_minute: float
    conversion_per_km: float = 0.0
    step_multiplier: float = 1.0


class ConversionRuleUpdate(BaseModel):
    conversion_per_minute: Optional[float] = None
    conversion_per_km: Optional[float] = None
    step_multiplier: Optional[float] = None


class UserSettingsUpdate(BaseModel):
    name: Optional[str] = None
    weekly_goal: Optional[int] = None
    monthly_goal: Optional[int] = None


# Garmin
class GarminConnectRequest(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    mfa_session_id: Optional[str] = None
    mfa_code: Optional[str] = None


class GarminSyncRequest(BaseModel):
    start_date: date
    end_date: date


class GarminStatusResponse(BaseModel):
    connected: bool
    email: Optional[str] = None
    mfa_session_id: Optional[str] = None


class GarminSyncResponse(BaseModel):
    imported: int
    skipped: int
    steps_updated: int
    health_synced: int = 0
    warnings: list[str] = []
