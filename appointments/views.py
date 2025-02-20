from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from .models import TimeSlot, Appointment
from users.models import User
from django.core.exceptions import ValidationError  
from django.shortcuts import render, redirect, get_object_or_404
import uuid
import requests

@login_required
def manage_slots(request):
    if not request.user.is_doctor:
        return redirect('dashboard')

    if request.method == "POST":
        # Handle slot creation
        if "create_slot" in request.POST:
            try:
                date = request.POST.get("date")
                start_time = request.POST.get("start_time")
                end_time = request.POST.get("end_time")

                slot = TimeSlot(
                    doctor=request.user,
                    date=date,
                    start_time=start_time,
                    end_time=end_time
                )
                slot.full_clean()
                slot.save()
                messages.success(request, "Time slot created successfully!")
            except ValidationError as e:
                messages.error(request, str(e))
            except Exception as e:
                messages.error(request, f"Error: {str(e)}")

        # Handle slot deletion
        elif "delete_slot" in request.POST:
            slot_id = request.POST.get("slot_id")
            try:
                slot = TimeSlot.objects.get(id=slot_id, doctor=request.user)
                if slot.is_booked:
                    messages.error(request, "Cannot delete booked slots")
                else:
                    slot.delete()
                    messages.success(request, "Slot deleted successfully")
            except TimeSlot.DoesNotExist:
                messages.error(request, "Slot not found")

    slots = TimeSlot.objects.filter(doctor=request.user).order_by("date", "start_time")
    return render(request, "appointments/manage_slots.html", {
        "slots": slots,
        "today": timezone.now().date().isoformat()
    })

@login_required
@transaction.atomic
def client_book_appointment(request):
    if not request.user.is_client:
        return redirect('dashboard')

    if request.method == "POST":
        slot_id = request.POST.get("slot_id")
        try:
            # Lock the slot for update
            slot = TimeSlot.objects.select_for_update().get(id=slot_id, is_booked=False)
            
            # Convert to timezone-aware datetime
            naive_datetime = timezone.datetime.combine(slot.date, slot.start_time)
            aware_datetime = timezone.make_aware(naive_datetime)

            # Create appointment within transaction
            Appointment.objects.create(
                doctor=slot.doctor,
                client=request.user,
                date=aware_datetime,
                time_slot=slot,
                status="Pending"
            )
            
            # Update slot status
            slot.is_booked = True
            slot.save()

            messages.success(request, "Appointment booked successfully!")
            return redirect('dashboard')
            
        except TimeSlot.DoesNotExist:
            messages.error(request, "Slot is already booked or does not exist.")
        except Exception as e:
            messages.error(request, f"Error booking appointment: {str(e)}")
        
        return redirect('book_appointment')

    slots = TimeSlot.objects.filter(is_booked=False)
    return render(request, "appointments/book_appointment.html", {"slots": slots})

@login_required
def video_call(request, room_id):
    appointment = get_object_or_404(Appointment, room_id=room_id)
    
    # Verify participant
    if request.user not in [appointment.doctor, appointment.client]:
        return redirect('dashboard')
    
    return render(request, 'appointments/video_call.html', {
        'room_id': room_id,
        'appointment': appointment
    })

@login_required
def confirm_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.user != appointment.doctor:
        return redirect('dashboard')
    
    appointment.status = 'Confirmed'
    appointment.generate_room_id()
    appointment.save()
    return redirect('dashboard')

@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.user not in [appointment.doctor, appointment.client]:
        return redirect('dashboard')
    
    # Get the associated time slot (assuming a ForeignKey relationship)
    time_slot = appointment.time_slot
    
    # Free the time slot (e.g., mark it as available)
    time_slot.is_booked = False  # Adjust based on your TimeSlot model
    time_slot.save()

    messages.success(request, "Appointment canceled successfully. The time slot is now available.")

    appointment.status = 'cancelled'
    appointment.save()
    return redirect('dashboard')

