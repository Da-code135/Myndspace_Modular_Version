from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.db.models import OuterRef, Subquery, Q 
from .forms import CustomUserCreationForm
from .models import User
from appointments.models import Appointment, TimeSlot
from chat.models import ChatRoom, ChatMessage

@login_required
def dashboard_view(request):
    # Appointments
    if request.user.is_doctor:
        appointments = Appointment.objects.filter(
            doctor=request.user,
            date__gte=timezone.now()
        ).order_by('date')[:5]
        time_slots = TimeSlot.objects.filter(
            doctor=request.user,
            date__gte=timezone.now().date()
        ).order_by("date", "start_time")[:5]
    else:
        appointments = Appointment.objects.filter(
            client=request.user,
            date__gte=timezone.now()
        ).order_by('date')[:5]
        time_slots = None

    # Chat data
    active_chats = ChatRoom.objects.filter(
        Q(doctor=request.user) | Q(client=request.user)
    ).annotate(
        last_message=Subquery(
            ChatMessage.objects.filter(
                room=OuterRef('pk')
            ).order_by('-timestamp').values('timestamp')[:1]
        )
    ).order_by('-last_message')[:5]

    # Unread messages count
    unread_count = ChatMessage.objects.filter(
        room__in=active_chats,
        read=False
    ).exclude(sender=request.user).count()

    return render(request, 'dashboard.html', {
        'appointments': appointments,
        'time_slots': time_slots,
        'active_chats': active_chats,
        'unread_count': unread_count
    })

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('profile_setup')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = CustomUserCreationForm()
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            if not user.is_verified:
                return redirect('profile_setup')
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'users/login.html')

@login_required
def profile_setup_view(request):
    user = request.user
    if request.method == 'POST':
        if user.is_doctor:
            specialization = request.POST.get('specialization')
            experience = request.POST.get('experience')
            user.doctor_profile.specialization = specialization
            user.doctor_profile.experience = experience
            user.doctor_profile.save()
        
        user.is_verified = True
        user.save()
        messages.success(request, 'Profile setup complete!')
        return redirect('dashboard')
    
    return render(request, 'users/profile_setup.html', {'user': user})

def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('landing_page')

# Landing Page View
def landing_page(request):
    """Render the landing page for unauthenticated users."""
    return render(request, 'landing_page.html')
