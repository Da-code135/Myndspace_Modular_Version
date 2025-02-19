from django.urls import path
from . import views

urlpatterns = [
    path('manage-slots/', views.doctor_manage_slots, name='manage_slots'),
    path('book-appointment/', views.client_book_appointment, name='book_appointment'),
    path('confirm-appointment/<int:appointment_id>/', views.confirm_appointment, name='confirm_appointment'),
    path('cancel-appointment/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('zoom/authorize/', views.zoom_authorize, name='zoom_authorize'),
    path('zoom/callback/', views.zoom_callback, name='zoom_callback'),
]