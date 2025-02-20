from django.urls import path
from . import views

urlpatterns = [
    path(' ', views.chat_landing, name='chat_landing'),
    path('list/', views.chat_list, name='chat_list'),  # Keep existing if needed
    path('start/', views.start_chat_selection, name='start_chat_selection'),
    path('room/<int:room_id>/', views.chat_room, name='chat_room'),
    path('start/<int:user_id>/', views.start_chat, name='start_chat'),
]