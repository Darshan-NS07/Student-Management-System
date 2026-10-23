
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CourseCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    code: str = Field(min_length=2, max_length=20, pattern=r"^[A-Za-z0-9_-]+$")
    description: str = Field(default="", max_length=1000)
    instructor: str = Field(min_length=2, max_length=100)
    duration_weeks: int = Field(ge=1, le=520)

    @field_validator("title", "instructor")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2 or not any(char.isalpha() for char in value):
            raise ValueError("Must contain at least two characters and a letter.")
        if any(not (char.isalpha() or char.isspace() or char in "-'.") for char in value):
            raise ValueError("Contains invalid characters.")
        return value

    @field_validator("code")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.strip().upper()

    @field_validator("description")
    @classmethod
    def normalize_description(cls, value: str) -> str:
        return value.strip()


class CourseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=120)
    code: str | None = Field(default=None, min_length=2, max_length=20, pattern=r"^[A-Za-z0-9_-]+$")
    description: str | None = Field(default=None, max_length=1000)
    instructor: str | None = Field(default=None, min_length=2, max_length=100)
    duration_weeks: int | None = Field(default=None, ge=1, le=520)
    is_active: bool | None = None

    @field_validator("title", "instructor")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if len(value) < 2 or not any(char.isalpha() for char in value):
            raise ValueError("Must contain at least two characters and a letter.")
        if any(not (char.isalpha() or char.isspace() or char in "-'.") for char in value):
            raise ValueError("Contains invalid characters.")
        return value

    @field_validator("code")
    @classmethod
    def normalize_optional_code(cls, value: str | None) -> str | None:
        return value.strip().upper() if value is not None else None

    @field_validator("description")
    @classmethod
    def normalize_optional_description(cls, value: str | None) -> str | None:
        return value.strip() if value is not None else None


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    code: str
    description: str
    instructor: str
    duration_weeks: int
    is_active: bool
    created_at: datetime
