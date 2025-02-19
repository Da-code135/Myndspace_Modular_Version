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
    
    # Zoom integration fields
    zoom_access_token = models.CharField(max_length=255, blank=True, null=True)
    zoom_refresh_token = models.CharField(max_length=255, blank=True, null=True)
    zoom_token_expires_at = models.DateTimeField(blank=True, null=True)

    def refresh_zoom_token(self):
        """Instance method to refresh token (alternative approach)"""
        if self.zoom_token_expires_at and self.zoom_token_expires_at > timezone.now():
            return self.zoom_access_token
        
        try:
            response = requests.post(
                settings.ZOOM_TOKEN_URL,
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.zoom_refresh_token
                },
                auth=(settings.ZOOM_CLIENT_ID, settings.ZOOM_CLIENT_SECRET)
            )
            response.raise_for_status()
            
            tokens = response.json()
            self.zoom_access_token = tokens["access_token"]
            self.zoom_refresh_token = tokens["refresh_token"]
            self.zoom_token_expires_at = timezone.now() + timedelta(seconds=tokens["expires_in"])
            self.save()
            return self.zoom_access_token
        
        except Exception as e:
            print(f"Failed to refresh Zoom token: {str(e)}")
            return None

    def __str__(self):
        return f"{self.user.username}'s Profile"