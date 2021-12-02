from django import forms
from .models import Event
from django.core.exceptions import ValidationError
from django.utils import timezone
tz = timezone.get_default_timezone()

class EventForm(forms.ModelForm):
    date_date = forms.CharField(max_length=40, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    date_time = forms.CharField(max_length=40, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = Event
        fields = ['title', 'abstract', 'description', 'date_date', 'date_time', 'duration', 'language', 'persons', 'room', 'track', 'url', 'videofile']

    def __init__(self, *args, initial={}, **kwargs):
        if 'instance' in kwargs:
            initial["date_date"] = kwargs['instance'].date.astimezone(tz).strftime("%Y-%m-%d")
            initial["date_time"] = kwargs['instance'].date.astimezone(tz).strftime("%H:%M")
            self.new = False
        else:
            self.new = True

        forms.ModelForm.__init__(self, *args, **kwargs, initial=initial)
