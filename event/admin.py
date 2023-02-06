from django.contrib import admin
from .models import Conference, Event


class ConferenceAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'voctoweb_slug', 'tracker_project_id')
    save_as = True
    ordering = ('-id', )

admin.site.register(Conference, ConferenceAdmin)

class EventAdmin(admin.ModelAdmin):
    list_display = ('conference', 'talkid', 'title', 'date', 'persons')
    ordering = ('-date', )

admin.site.register(Event, EventAdmin)
