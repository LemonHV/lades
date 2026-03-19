from typing import cast
from uuid import uuid4

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.utils.timezone import now


class UserManager(BaseUserManager):
    use_in_migrations = True

    def normalize_email_value(self, email: str) -> str:
        if not email:
            raise ValueError("Email is required.")
        return self.normalize_email(email).strip().lower()

    def create_user(self, email: str, password=None, **extra_fields) -> "User":
        email = self.normalize_email_value(email)
        user = cast("User", self.model(email=email, **extra_fields))

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.full_clean()
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password=None, **extra_fields) -> "User":
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_active") is not True:
            raise ValueError("Superuser must have is_active=True.")
        if not password:
            raise ValueError("Superuser must have a password.")

        return self.create_user(email=email, password=password, **extra_fields)

    def get_by_natural_key(self, email):
        return self.get(
            **{self.model.USERNAME_FIELD: self.normalize_email_value(email)}
        )


class User(AbstractBaseUser, PermissionsMixin):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    email = models.EmailField(max_length=255, unique=True, db_index=True)
    google_id = models.CharField(max_length=255, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100, blank=True, default="")
    is_staff = models.BooleanField(default=False, db_index=True)
    is_active = models.BooleanField(default=True, db_index=True)
    date_joined = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["is_active", "is_staff"]),
            models.Index(fields=["date_joined"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=~Q(email=""),
                name="user_email_not_empty",
            ),
        ]

    def clean(self):
        super().clean()

        self.email = User.objects.normalize_email_value(self.email)
        self.name = (self.name or "").strip()

        if self.name and len(self.name) < 2:
            raise ValidationError({
                "name": "Name must be at least 2 characters long."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.email


class AuthenticateToken(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="authenticate_tokens",
        db_index=True,
    )
    token = models.CharField(max_length=255, unique=True, db_index=True)
    expires_at = models.DateTimeField(db_index=True)
    blacklisted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "expires_at"]),
            models.Index(fields=["user", "blacklisted_at"]),
            models.Index(fields=["token"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=~Q(token=""),
                name="auth_token_not_empty",
            ),
        ]

    def clean(self):
        super().clean()

        self.token = (self.token or "").strip()

        if not self.token:
            raise ValidationError({"token": "Token is required."})

        if self.blacklisted_at and self.created_at and self.blacklisted_at < self.created_at:
            raise ValidationError({
                "blacklisted_at": "blacklisted_at cannot be earlier than created_at."
            })

        if self.expires_at and self.created_at and self.expires_at < self.created_at:
            raise ValidationError({
                "expires_at": "expires_at cannot be earlier than created_at."
            })

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    @property
    def is_blacklisted(self) -> bool:
        return self.blacklisted_at is not None

    @property
    def is_expired(self) -> bool:
        return self.expires_at < now()

    @property
    def is_available(self) -> bool:
        return not self.is_blacklisted and not self.is_expired

    def __str__(self):
        return f"{self.user.email} - {self.token[:12]}"


class ShippingInfo(models.Model):
    uid = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="shipping_infos",
        db_index=True,
    )
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "is_default"]),
            models.Index(fields=["user", "created_at"]),
        ]
        constraints = [
            models.CheckConstraint(
                check=~Q(name=""),
                name="shipping_info_name_not_empty",
            ),
            models.CheckConstraint(
                check=~Q(phone=""),
                name="shipping_info_phone_not_empty",
            ),
            models.CheckConstraint(
                check=~Q(address=""),
                name="shipping_info_address_not_empty",
            ),
            models.UniqueConstraint(
                fields=["user"],
                condition=Q(is_default=True),
                name="unique_default_shipping_info_per_user",
            ),
        ]

    def clean(self):
        super().clean()

        self.name = (self.name or "").strip()
        self.phone = (self.phone or "").strip()
        self.address = (self.address or "").strip()

        if not self.name:
            raise ValidationError({"name": "Name is required."})
        if len(self.name) < 2:
            raise ValidationError({"name": "Name must be at least 2 characters long."})

        if not self.phone:
            raise ValidationError({"phone": "Phone is required."})

        normalized_phone = (
            self.phone.replace(" ", "")
            .replace(".", "")
            .replace("-", "")
        )

        if not normalized_phone.isdigit():
            raise ValidationError({"phone": "Phone must contain digits only."})

        if len(normalized_phone) < 9 or len(normalized_phone) > 15:
            raise ValidationError({"phone": "Phone must be between 9 and 15 digits."})

        self.phone = normalized_phone

        if not self.address:
            raise ValidationError({"address": "Address is required."})
        if len(self.address) < 5:
            raise ValidationError({"address": "Address is too short."})

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.email} - {self.name}"