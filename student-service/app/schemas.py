
import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class StudentCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    phone: str = Field(min_length=10, max_length=20)
    department: str = Field(min_length=2, max_length=100)
    course: str = Field(min_length=2, max_length=100)

    @field_validator("name", "department", "course")
    @classmethod
    def validate_text(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2 or not any(char.isalpha() for char in value):
            raise ValueError("Must contain at least two characters and a letter.")
        if any(not (char.isalpha() or char.isspace() or char in "-'&.") for char in value):
            raise ValueError("Contains invalid characters.")
        return value

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: EmailStr) -> EmailStr:
      return str(value).strip().lower()

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"\+?[0-9][0-9 ()-]{8,18}[0-9]", value):
            raise ValueError("Enter a valid phone number.")
        if sum(char.isdigit() for char in value) < 10:
            raise ValueError("Phone number must contain at least 10 digits.")
        return value


class StudentUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, min_length=10, max_length=20)
    department: str | None = Field(default=None, min_length=2, max_length=100)
    course: str | None = Field(default=None, min_length=2, max_length=100)

    @field_validator("name", "department", "course")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if len(value) < 2 or not any(char.isalpha() for char in value):
            raise ValueError("Must contain at least two characters and a letter.")
        if any(not (char.isalpha() or char.isspace() or char in "-'&.") for char in value):
            raise ValueError("Contains invalid characters.")
        return value

    @field_validator("email")
    @classmethod
    def normalize_optional_email(cls, value: EmailStr | None) -> EmailStr | None:
       return str(value).strip().lower() if value is not None else None

    @field_validator("phone")
    @classmethod
    def validate_optional_phone(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not re.fullmatch(r"\+?[0-9][0-9 ()-]{8,18}[0-9]", value) or sum(char.isdigit() for char in value) < 10:
            raise ValueError("Enter a valid phone number with at least 10 digits.")
        return value


class StudentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    phone: str
    department: str
    course: str
    created_at: datetime
