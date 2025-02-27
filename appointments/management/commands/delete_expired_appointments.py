from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from appointments.models import Appointment

class Command(BaseCommand):
    help = 'Deletes appointments that have passed their end time'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        today = now.date()
        current_time = now.time()

        # Get expired appointments
        expired = Appointment.objects.filter(
            Q(time_slot__date__lt=today) |  # Date is in the past
            Q(time_slot__date=today, time_slot__end_time__lte=current_time)  # Today but time passed
        )

        # Free time slots and delete appointments
        for appointment in expired:
            if appointment.time_slot:
                appointment.time_slot.is_booked = False
                appointment.time_slot.save()
            appointment.delete()

        self.stdout.write(f"Deleted {len(expired)} expired appointments")
