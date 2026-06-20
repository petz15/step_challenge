from sqlalchemy import Column, Integer, String, Float, Boolean, Date, Text, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from database import Base


class ActivityTypeEnum(str, enum.Enum):
    Walking = "Walking"
    Running = "Running"
    Hiking = "Hiking"
    Cycling = "Cycling"
    Climbing = "Climbing"
    Strength = "Strength"
    Manual_Steps = "Manual Steps"


class SourceEnum(str, enum.Enum):
    manual = "manual"
    garmin_api = "garmin_api"
    csv_import = "csv_import"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    name = Column(String, nullable=False)
    weekly_goal = Column(Integer, nullable=True)
    monthly_goal = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    is_superuser = Column(Boolean, default=False, nullable=False)
    garmin_email = Column(String, nullable=True)
    garmin_password_enc = Column(Text, nullable=True)

    activities = relationship("Activity", back_populates="user")


class Activity(Base):
    __tablename__ = "activities"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String, nullable=False)
    duration_minutes = Column(Float, nullable=True)
    distance_km = Column(Float, nullable=True)
    manual_steps = Column(Integer, nullable=True)
    step_equivalent_calculated = Column(Integer, nullable=False, default=0)
    date = Column(Date, nullable=False)
    notes = Column(Text, nullable=True)
    source = Column(String, nullable=False, default="manual")
    garmin_activity_id = Column(String, nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    user = relationship("User", back_populates="activities")


class HealthMetric(Base):
    __tablename__ = "health_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    metric_type = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    source = Column(String, nullable=False, default="garmin_api")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ConversionRule(Base):
    __tablename__ = "conversion_rules"

    id = Column(Integer, primary_key=True, index=True)
    activity_type = Column(String, unique=True, nullable=False, index=True)
    conversion_per_minute = Column(Float, nullable=False, default=0.0)
    conversion_per_km = Column(Float, nullable=False, default=0.0)
    step_multiplier = Column(Float, nullable=False, default=1.0)
    is_default = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
