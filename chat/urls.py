from django.urls import path
from . import views

urlpatterns = [
    path('', views.chat_list, name='chat_list'),
    path('<int:room_id>/', views.chat_room, name='chat_room'),
    path('start/<int:user_id>/', views.start_chat, name='start_chat'),
]