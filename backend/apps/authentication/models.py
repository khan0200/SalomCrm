import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone

class UserRole(models.TextChoices):
    SUPER_ADMIN = 'SUPER_ADMIN', 'Platform Super Admin'
    HEAD_MANAGER = 'HEAD_MANAGER', 'Tenant Head Manager'
    MANAGER = 'MANAGER', 'Tenant Manager'
    STAFF = 'STAFF', 'Tenant Staff'


class CustomUserManager(BaseUserManager):
    """Manager for custom user model using email as unique identifier."""
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email address is required')
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', UserRole.SUPER_ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom User model representing CRM users and Platform Super Admins.
    Every tenant user belongs to a specific tenant. Platform Super Admins have tenant=None.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True, max_length=255, db_index=True)
    full_name = models.CharField(max_length=255)
    role = models.CharField(
        max_length=32,
        choices=UserRole.choices,
        default=UserRole.STAFF,
        db_index=True
    )
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        db_index=True
    )
    branch = models.ForeignKey(
        'tenants.Branch',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['full_name']

    class Meta:
        db_table = 'crm_users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        tenant_str = f" [{self.tenant.name}]" if self.tenant else " [Global Super Admin]"
        return f"{self.full_name} ({self.email}){tenant_str}"

    @property
    def is_platform_super_admin(self):
        return self.is_superuser or self.role == UserRole.SUPER_ADMIN

    @property
    def is_head_manager(self):
        return self.role == UserRole.HEAD_MANAGER

    @property
    def is_manager(self):
        return self.role in (UserRole.HEAD_MANAGER, UserRole.MANAGER)
