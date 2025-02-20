from django.urls import path
from . import views

app_name = 'steamroomandselfcare'

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('breathing/', views.breathing_exercise, name='breathing_exercise'),
    path('journaling/', views.journaling_prompt, name='journaling_prompt'),
    path('thought-logs/', views.thought_log, name='thought_log'),
    path('meditation/', views.meditation, name='meditation'),
]