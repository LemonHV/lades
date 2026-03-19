from uuid import UUID

from ninja import Schema
from pydantic import field_validator


class ShippingInfoCreateSchema(Schema):
    name: str
    phone: str
    address: str
    is_default: bool = False

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str):
        v = v.strip()
        if not v:
            raise ValueError("Name is required")
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Name is too long")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str):
        v = v.strip().replace(" ", "").replace(".", "").replace("-", "")
        if not v:
            raise ValueError("Phone is required")
        if not v.isdigit():
            raise ValueError("Phone must contain digits only")
        if len(v) < 9 or len(v) > 15:
            raise ValueError("Phone must be between 9 and 15 digits")
        return v

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str):
        v = v.strip()
        if not v:
            raise ValueError("Address is required")
        if len(v) < 5:
            raise ValueError("Address is too short")
        if len(v) > 255:
            raise ValueError("Address is too long")
        return v


class ShippingInfoUpdateSchema(Schema):
    name: str | None = None
    phone: str | None = None
    address: str | None = None
    is_default: bool | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None):
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be empty")
        if len(v) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(v) > 100:
            raise ValueError("Name is too long")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str | None):
        if v is None:
            return v
        v = v.strip().replace(" ", "").replace(".", "").replace("-", "")
        if not v:
            raise ValueError("Phone cannot be empty")
        if not v.isdigit():
            raise ValueError("Phone must contain digits only")
        if len(v) < 9 or len(v) > 15:
            raise ValueError("Phone must be between 9 and 15 digits")
        return v

    @field_validator("address")
    @classmethod
    def validate_address(cls, v: str | None):
        if v is None:
            return v
        v = v.strip()
        if not v:
            raise ValueError("Address cannot be empty")
        if len(v) < 5:
            raise ValueError("Address is too short")
        if len(v) > 255:
            raise ValueError("Address is too long")
        return v


class ShippingInfoResponseSchema(Schema):
    uid: UUID
    name: str
    phone: str
    address: str
    is_default: bool
