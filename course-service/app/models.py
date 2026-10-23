
from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from app.database import Base


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(120), nullable=False, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True)
    description = Column(String(1000), nullable=False, default="")
    instructor = Column(String(100), nullable=False)
    duration_weeks = Column(Integer, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
