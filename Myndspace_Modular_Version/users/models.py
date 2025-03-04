from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
import requests
import pytz

class User(AbstractUser):
    is_doctor = models.BooleanField(default=False)
    is_client = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        choices=[(tz, tz) for tz in pytz.all_timezones])
    
    def clean(self):
        if self.is_doctor and self.is_client:
            raise ValidationError("User cannot be both doctor and client.")
        super().clean()

class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="doctor_profile")
    specialization = models.CharField(max_length=100, default="General")
    experience = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"

class ClientProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="client_profile")
    condition = models.CharField(max_length=100, default="General")