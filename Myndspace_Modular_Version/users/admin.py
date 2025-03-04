from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, DoctorProfile

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'is_doctor', 'is_client', 'is_verified')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('email',)}),
        ('Permissions', {'fields': ('is_doctor', 'is_client', 'is_verified')}),
    )

admin.site.register(User, CustomUserAdmin)
admin.site.register(DoctorProfile)