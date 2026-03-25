from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class UserRole(models.TextChoices):
    SUPER_ADMIN = 'SUPER_ADMIN', _('Super Admin')
    COOP_ADMIN = 'COOP_ADMIN', _('Cooperative Admin')
    MEMBER = 'MEMBER', _('Member')

class User(AbstractUser):
    role = models.CharField(max_length=20, choices=UserRole.choices, default=UserRole.MEMBER)
    cooperative = models.ForeignKey(
        'cooperatives.Cooperative', on_delete=models.CASCADE, null=True, blank=True, related_name='users'
    )
    phone = models.CharField(max_length=20, null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    is_active_member = models.BooleanField(default=True)
    join_date = models.DateField(null=True, blank=True)
    is_suspended = models.BooleanField(default=False)
    joined_at = models.DateTimeField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('M','Male'),('F','Female'),('O','Other')], null=True, blank=True)
    must_change_password = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.get_full_name()} ({self.username})"

    @property
    def status_label(self):
        if self.is_suspended:
            return 'suspended'
        return 'active' if self.is_active_member else 'inactive'
