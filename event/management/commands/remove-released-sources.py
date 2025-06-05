from django.core.management.base import BaseCommand, CommandError
from event.models import Event
import requests
import os
from django.utils import timezone

class Command(BaseCommand):
    help = 'Removes source files for videos that have already been published on media.ccc.de'

    def handle(self, *args, **options):
        now = timezone.now()
        for event in Event.objects.filter(published=True).order_by("talkid"):
            if not event.videofile: continue # skip if no videofile exists to begin with
            if not os.path.exists("/var/lib/voctoimport/uploads/%s" % event.videofile): continue # skip if file is already deleted
            if (now - event.date).total_seconds() < 1*31*24*60*60: continue # skip if event is younger than one month
            apievent = requests.get("https://media.ccc.de/public/events/%s" % event.guid).json()
            if "message" in apievent and apievent["message"] == "not found": continue # skip if guid can't be found on media
            if apievent['slug'] != event.slug: continue # skip if slug doesn't match
            if len(apievent["recordings"]) < 2: continue # skip if no recordings have been published yet

            print("Removing source for %s..." % event.slug)
            os.remove("/var/lib/voctoimport/uploads/%s" % event.videofile)
