from django.db import models
from django.conf import settings
from django.utils import timezone

class ChatRoom(models.Model):
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="doctor_rooms")  # Use settings.AUTH_USER_MODEL
    client = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="client_rooms")  # Use settings.AUTH_USER_MODEL
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('doctor', 'client')

    def __str__(self):
        return f"Chat between {self.doctor} and {self.client}"


class ChatMessage(models.Model):
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Use settings.AUTH_USER_MODEL
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    delivered = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.sender.username} - {self.timestamp}"