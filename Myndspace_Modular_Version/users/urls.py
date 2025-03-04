from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('profile-setup/', views.profile_setup_view, name='profile_setup'),
    path('logout/', views.logout_view, name='logout'),
]
