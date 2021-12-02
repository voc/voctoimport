from django.contrib import admin
from .models import Conference, Event

admin.site.register(Conference)

class EventAdmin(admin.ModelAdmin):
    list_display = ('conference', 'talkid', 'title', 'date', 'persons')
    ordering = ('-date', )

admin.site.register(Event, EventAdmin)
