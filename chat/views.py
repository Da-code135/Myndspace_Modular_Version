from django.db.models import Q, Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ChatRoom, ChatMessage
from users.models import User
from django.conf import settings


@login_required
def chat_landing(request):
    if request.user.is_doctor:
        rooms = ChatRoom.objects.filter(doctor=request.user)
    else:
        rooms = ChatRoom.objects.filter(client=request.user)
    
    # Annotate rooms with unread count using Q objects
    rooms = rooms.annotate(
        unread_count=Count(
            'messages',
            filter=Q(messages__read=False) & ~Q(messages__sender=request.user)
        )
    )
    
    unread_count = sum(room.unread_count for room in rooms)
    
    return render(request, 'chat/chat_landing.html', {
        'active_chats': rooms,
        'unread_count': unread_count
    })

@login_required
def chat_list(request):
    if request.user.is_doctor:
        rooms = ChatRoom.objects.filter(doctor=request.user)
    else:
        rooms = ChatRoom.objects.filter(client=request.user)
    return render(request, 'chat/list.html', {'rooms': rooms})

@login_required
def chat_room(request, room_id):
    room = get_object_or_404(ChatRoom, id=room_id)
    
    if request.user not in [room.doctor, room.client]:
        return redirect('chat_list')
    
    messages = ChatMessage.objects.filter(room=room).order_by('timestamp')
    return render(request, 'chat/room.html', {
        'room': room,
        'messages': messages,
       
    })

@login_required
def start_chat(request, user_id):
    
    target_user = get_object_or_404(User, id=user_id)
    if request.user.is_doctor and target_user.is_client:
        room, created = ChatRoom.objects.get_or_create(
            doctor=request.user,
            client=target_user
        )
    elif request.user.is_client and target_user.is_doctor:
        room, created = ChatRoom.objects.get_or_create(
            doctor=target_user,
            client=request.user
        )
    else:
        return redirect('dashboard')
    
    return redirect('chat_room', room_id=room.id)

@login_required
def start_chat_selection(request):
    if request.user.is_doctor:
        # Show all clients for doctors
        users = User.objects.filter(is_client=True)
    else:
        # Show all doctors for clients
        users = User.objects.filter(is_doctor=True)
    
    return render(request, 'chat/start_chat.html', {
        'users': users
    })