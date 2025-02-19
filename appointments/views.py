from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.conf import settings
from .models import TimeSlot, Appointment
from users.models import User
from django.core.exceptions import ValidationError  
import requests

@login_required
def doctor_manage_slots(request):
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
def client_book_appointment(request):
    if not request.user.is_client:
        return redirect('dashboard')

    if request.method == "POST":
        slot_id = request.POST.get("slot_id")
        try:
            slot = TimeSlot.objects.get(id=slot_id, is_booked=False)
            Appointment.objects.create(
                doctor=slot.doctor,
                client=request.user,
                date=timezone.datetime.combine(slot.date, slot.start_time),
                time_slot=slot,
                status="Pending"
            )
            slot.is_booked = True
            slot.save()
            messages.success(request, "Appointment booked successfully!")
            return redirect('dashboard')
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('book_appointment')

    slots = TimeSlot.objects.filter(is_booked=False)
    return render(request, "appointments/book_appointment.html", {"slots": slots})

@login_required
def confirm_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    if request.user != appointment.doctor:
        return redirect('dashboard')

    if not request.user.doctor_profile.zoom_access_token:
        messages.error(request, "Please connect your Zoom account first!")
        return redirect('profile_setup')

    try:
        # Create Zoom meeting
        zoom_link = create_zoom_meeting(request.user, appointment.date)
        if zoom_link:
            appointment.zoom_meeting_link = zoom_link
            appointment.status = "Confirmed"
            appointment.save()
            messages.success(request, "Appointment confirmed with Zoom link!")
        else:
            messages.error(request, "Failed to create Zoom meeting")
    except Exception as e:
        messages.error(request, f"Error creating meeting: {str(e)}")

    return redirect('dashboard')

@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)
    if request.user not in [appointment.doctor, appointment.client]:
        return redirect('dashboard')
    
    appointment.cancel()
    return redirect('dashboard')

# Zoom Integration Views
def create_zoom_meeting(user, appointment_time):
    """Creates a Zoom meeting using the doctor's account."""
    doctor_profile = user.doctor_profile
    access_token = refresh_zoom_token(doctor_profile)

    if not access_token:
        return None

    url = f"{settings.ZOOM_API_URL}users/me/meetings"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }
    
    # Calculate end time (30 minutes after start)
    end_time = appointment_time + timedelta(minutes=30)

    data = {
        "topic": "Myndspace Appointment",
        "type": 2,  # Scheduled meeting
        "start_time": appointment_time.isoformat(),
        "duration": 30,
        "timezone": str(user.timezone),  # Add timezone to User model
        "settings": {
            "join_before_host": False,
            "waiting_room": True,
        }
    }

    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        return response.json().get("join_url")
    except requests.exceptions.RequestException as e:
        print(f"Zoom API Error: {str(e)}")
        return None

@login_required
def zoom_authorize(request):
    if not request.user.is_doctor:
        return redirect('dashboard')
    
    auth_url = f"{settings.ZOOM_AUTH_URL}?response_type=code&client_id={settings.ZOOM_CLIENT_ID}&redirect_uri={settings.ZOOM_REDIRECT_URI}"
    return redirect(auth_url)

@login_required
def zoom_callback(request):
    if not request.user.is_doctor:
        return redirect('dashboard')
    
    code = request.GET.get("code")
    if not code:
        return redirect('dashboard')
    
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": settings.ZOOM_REDIRECT_URI
    }
    
    response = requests.post(
        settings.ZOOM_TOKEN_URL,
        data=data,
        auth=(settings.ZOOM_CLIENT_ID, settings.ZOOM_CLIENT_SECRET)
    )
    
    if response.status_code == 200:
        tokens = response.json()
        doctor_profile = request.user.doctor_profile
        doctor_profile.zoom_access_token = tokens["access_token"]
        doctor_profile.zoom_refresh_token = tokens["refresh_token"]
        doctor_profile.save()
    
    return redirect('dashboard')

def refresh_zoom_token(doctor_profile):
    """Refresh the Zoom access token if expired."""
    if doctor_profile.zoom_token_expires_at and doctor_profile.zoom_token_expires_at > timezone.now():
        return doctor_profile.zoom_access_token
    
    try:
        response = requests.post(
            settings.ZOOM_TOKEN_URL,
            data={
                "grant_type": "refresh_token",
                "refresh_token": doctor_profile.zoom_refresh_token
            },
            auth=(settings.ZOOM_CLIENT_ID, settings.ZOOM_CLIENT_SECRET)
        )
        response.raise_for_status()
        
        tokens = response.json()
        doctor_profile.zoom_access_token = tokens["access_token"]
        doctor_profile.zoom_refresh_token = tokens["refresh_token"]
        doctor_profile.zoom_token_expires_at = timezone.now() + timezone.timedelta(seconds=tokens["expires_in"])
        doctor_profile.save()
        return doctor_profile.zoom_access_token
    
    except Exception as e:
        print(f"Failed to refresh Zoom token: {str(e)}")
        return None