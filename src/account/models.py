from typing import cast
from uuid import uuid4

from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils.timezone import now


class Manager(BaseUserManager):
    use_in_migrations = True

    def create_user(self, identifier: str, password=None, **extra_fields) -> "User":
        if not identifier:
            raise ValueError("User must have a username")
        user = cast("User", self.model(identifier=identifier, **extra_fields))
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, identifier: str, password=None, **extra_fields):
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        return self.create_user(identifier, password, **extra_fields)

    def get_by_natural_key(self, identifier):
        return self.get(**{self.model.USERNAME_FIELD: identifier})


class User(AbstractBaseUser, PermissionsMixin):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100, blank=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(auto_now_add=True)
    objects = Manager()
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email or "AnonymousUser"


class ShippingAddress(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="shipping_address_fk_user",
        to_field="uid",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )

    address = models.CharField(max_length=255, null=False, blank=False)
    name = models.CharField(max_length=100, null=False, blank=False)
    phone = models.CharField(max_length=20, null=False, blank=False)
    is_default = models.BooleanField(default=False)


class AuthenticateToken(models.Model):
    user = models.ForeignKey(
        to=User,
        on_delete=models.CASCADE,
        related_name="authenticate_token_fk_user",
        to_field="uid",
        db_constraint=True,
        db_index=True,
        null=False,
        blank=False,
    )

    token = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        null=False,
        blank=False,
    )

    expires_at = models.DateTimeField(null=True, blank=True)
    blacklisted_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True, auto_now=False)
    updated_at = models.DateTimeField(auto_now=True, auto_now_add=False)

    @property
    def is_available(self) -> bool:
        return not self.blacklisted_at and (
            self.expires_at is not None and self.expires_at >= now()
        )
