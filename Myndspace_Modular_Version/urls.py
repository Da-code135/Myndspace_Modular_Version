from django.contrib import admin
from django.urls import path, include
from users import views as user_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', user_views.landing_page, name='landing_page'),
    path('dashboard/', user_views.dashboard_view, name='dashboard'),
    path('admin/', admin.site.urls),
    path('users/', include('users.urls')),
    path('appointments/', include('appointments.urls')),
    path('chat/', include('chat.urls')),
    path('selfcare/', include('steamroomandselfcare.urls', namespace='steamroomandselfcare')),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)