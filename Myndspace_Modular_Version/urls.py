from django.contrib import admin
from django.urls import path, include
from users import views as user_views

urlpatterns = [
    path('', user_views.landing_page, name='landing_page'),
    path('dashboard/', user_views.dashboard_view, name='dashboard'),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('appointments/', include('appointments.urls')),
    path('chat/', include('chat.urls')),
    path('selfcare/', include('steamroomandselfcare.urls', namespace='steamroomandselfcare')),
]