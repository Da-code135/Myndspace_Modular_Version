import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from Myndspace_Modular_Version import settings
from users.models import User

class TimeSlot(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="time_slots")
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("End time must be after start time.")
        
        # Check for overlapping slots
        overlapping = TimeSlot.objects.filter(
            doctor=self.doctor,
            date=self.date,
            start_time__lt=self.end_time,
            end_time__gt=self.start_time
        ).exclude(id=self.id)

        if overlapping.exists():
            raise ValidationError("This time slot overlaps with an existing slot.")

    def __str__(self):
        return f"{self.doctor.username} - {self.date} {self.start_time}-{self.end_time}"

class Appointment(models.Model):
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name="doctor_appointments")
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name="client_appointments")
    time_slot = models.OneToOneField(TimeSlot, on_delete=models.CASCADE, related_name="appointment", null=True, blank=True)
    date = models.DateTimeField()
    status = models.CharField(max_length=20, choices=[
        ("Pending", "Pending"),
        ("Confirmed", "Confirmed"),
        ("Cancelled", "Cancelled")
    ], default="Pending")
    room_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    notes = models.TextField(blank=True)
    

    def confirm(self):
        self.status = "Confirmed"
        if self.time_slot:
            self.time_slot.is_booked = True
            self.time_slot.save()
        self.save()

    def cancel(self):
        self.status = "Cancelled"
        if self.time_slot:
            self.time_slot.is_booked = False
            self.time_slot.save()
        self.save()

    def __str__(self):
        return f"Appointment {self.id} - {self.doctor} & {self.client}"

    def generate_room_id(self):
        if not self.room_id:
            self.room_id = uuid.uuid4()
        return self.room_id