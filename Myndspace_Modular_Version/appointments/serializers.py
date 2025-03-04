from rest_framework import serializers
from .models import TimeSlot

class TimeSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = TimeSlot
        fields = ['id', 'doctor', 'date', 'start_time', 'end_time', 'is_booked']
        read_only_fields = ['id', 'doctor', 'is_booked']
