from django import forms
from .models import ThoughtLog

class ThoughtLogForm(forms.ModelForm):
    class Meta:
        model = ThoughtLog
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5, 'cols': 50, 'placeholder': 'Write your thought...'}),
        }
