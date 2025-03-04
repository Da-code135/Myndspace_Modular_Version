from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, DoctorProfile

class CustomUserCreationForm(UserCreationForm):
    is_doctor = forms.BooleanField(
        required=False,
        label='Are you a doctor?',
        help_text='Check this if you are registering as a healthcare provider'
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'is_doctor']
        
    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_client = not self.cleaned_data.get('is_doctor', False)
        if commit:
            user.save()
            if user.is_doctor:
                DoctorProfile.objects.create(user=user)
        return user
