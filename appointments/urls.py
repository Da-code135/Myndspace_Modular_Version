from django.urls import path
from . import views

urlpatterns = [
    path('book-appointment/', views.client_book_appointment, name='book_appointment'),
    path('confirm-appointment/<int:appointment_id>/', views.confirm_appointment, name='confirm_appointment'),
    path('cancel-appointment/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('manage_slots/', views.manage_slots, name='manage_slots'),
    path('video/<uuid:room_id>/', views.video_call, name='video_call'),
]
