from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import ChatRoom, ChatMessage
from users.models import User

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
        'messages': messages
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