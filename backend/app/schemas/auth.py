"""Auth schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


def check_email(v) -> str:
    """Lenient email check: validate the syntax but allow special-use TLDs.

    We do a basic syntax check ourselves (RFC 5322 subset) and then use
    email_validator with `check_deliverability=False`. The latter still
    rejects some special-use TLDs, so we wrap that with a try/except and
    fall back to a regex-only check.

    Raises ValueError on bad syntax. Returns the normalized address.
    """
    if v is None or v == "":
        raise ValueError("email is required")
    s = str(v).strip()
    if len(s) > 254 or " " in s:
        raise ValueError("Invalid email")

    # Local part + @ + domain part
    import re
    if not re.match(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$", s):
        # Some users use a single-label domain (e.g. localhost in dev), so
        # also allow `[A-Za-z0-9.\-]+` without requiring a dot.
        if not re.match(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+$", s):
            raise ValueError("Invalid email")

    # Now try email-validator for the normalization
    try:
        import email_validator
        info = email_validator.validate_email(s, check_deliverability=False)
        return info.normalized
    except Exception:
        # email-validator still rejects some TLDs (e.g. .local); keep the
        # raw string and trust our regex check above.
        return s.lower()


class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=6, max_length=128)


class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(default="", max_length=120)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserOut"


class UserBase(BaseModel):
    email: str
    name: str = ""
    role: str = "editor"
    is_active: bool = True
    avatar_url: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    avatar_url: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8, max_length=128)
    role: Optional[str] = None
    is_active: Optional[bool] = None
    preferences: Optional[str] = None


class UserOut(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    updated_at: datetime


TokenResponse.model_rebuild()
