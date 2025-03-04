from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_landing, name='chat_landing'),
    path('list/', views.chat_list, name='chat_list'),  # Keep existing if needed
    path('start/', views.start_chat_selection, name='start_chat'),
    path('start/', views.start_chat_selection, name='start_chat_selection'),
    path('start/<int:user_id>/', views.start_chat, name='start_chat'), 
    path('room/<uuid:room_id>/', views.chat_room, name='chat_room'),
    path('messages/<uuid:room_id>/', views.get_chat_messages, name='chat_messages'),
    path('initiate_websocket/<uuid:room_id>/', views.initiate_websocket, name='initiate_websocket'),

]