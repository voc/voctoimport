from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
import uuid
from . import c3tt_rpc_client
from django.conf import settings
import datetime

LANGUAGES = {
    'en': 'Englisch',
    'de': 'Deutsch',
    'de-en': 'Deutsch (+Englisch)',
    'en-de': 'Englisch (+Deutsch)',
    'de-en-fr': 'Deutsch (+Englisch, +Französisch)',
    'de-en-it': 'Deutsch (+Englisch, +Italienisch)',
    'en-de-it': 'Englisch (+Deutsch, +Italienisch)',
    'en-de-fr': 'Englisch (+Deutsch, +Französisch)',
    'de-en-es': 'Deutsch (+Englisch, +Spanisch)',
    'en-de-es': 'Englisch (+Deutsch, +Spanisch)',
}

IMPORT_TOOL_TRACKER_PROJECT_ID = 362

class Conference(models.Model):
    title = models.CharField(max_length=200)
    slug = models.CharField(max_length=20)
    admins = models.ManyToManyField(get_user_model(), blank=True)
    tracker_project_id = models.IntegerField(blank=False, null=False, default=IMPORT_TOOL_TRACKER_PROJECT_ID)

    voctoweb_slug = models.CharField('Voctoweb Slug (Default: Use conference slug)', blank=True, null=True, max_length=200)
    voctoweb_path = models.CharField('Voctoweb Path (e.g. /cdn.media.ccc.de/contributors/myCoolName/)', blank=False, null=True, max_length=200)
    voctoweb_thumbpath = models.CharField('Voctoweb Thumbpath (e.g. /static.media.ccc.de/contributors/myCoolName/)', blank=False, null=True, max_length=200)

    youtube_token = models.CharField('YouTube Token (Default: Disable YouTube Upload)', blank=True, null=True, max_length=200)
    youtube_playlist = models.CharField('YouTube Playlist ID (Default: No playlist)', blank=True, null=True, max_length=200)

    def __str__(self):
        return "%s (%s)" % (self.title, self.slug)

def new_event_id():
    lasttalks = Event.objects.order_by('-talkid')
    if lasttalks.exists():
        return lasttalks.first().talkid + 1
    else:
        return 1

class Event(models.Model):
    guid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    talkid = models.IntegerField(unique=True, default=new_event_id)
    slug = models.SlugField(max_length=40, editable=False, blank=True)

    conference = models.ForeignKey(Conference, on_delete=models.CASCADE)

    title = models.CharField(max_length=200)
    abstract = models.TextField(blank=True)
    description = models.TextField(blank=True)
    date = models.DateTimeField()
    language = models.CharField(max_length=10, choices=LANGUAGES.items())
    persons = models.TextField()

    duration = models.CharField(max_length=5, default="01:00", blank=False, null=False)

    room = models.CharField(max_length=100, blank=True)
    track = models.CharField(max_length=100, blank=True)
    url = models.URLField(max_length=200, blank=True)

    published = models.BooleanField(default=False)

    def publish(self):
        c3tt = c3tt_rpc_client.C3TTClient(settings.CRS_URL, settings.CRS_GROUP, 'import.c3voc.de', settings.CRS_SECRET)
        props = {}

        # Meta
        props['Meta.Album'] = self.conference.title
        props['Meta.Year'] = str(datetime.datetime.now().year)

        # Publishing

        if self.conference.tracker_project_id == IMPORT_TOOL_TRACKER_PROJECT_ID:
            props['Publishing.Path'] = '/video/encoded/import/'
            props['Publishing.Base.Url'] = 'https://releasing.c3voc.de/releases/import/'
            props['Publishing.Mastodon.Enable'] = 'no'
            props['Publishing.Twitter.Enable'] = 'no'
            props['Publishing.UploadOptions'] = '-i /video/upload-key'
            props['Publishing.UploadTarget'] = 'upload@releasing.c3voc.de:/video/encoded/import'

        if self.conference.voctoweb_path:
            props['Publishing.Voctoweb.Path'] = self.conference.voctoweb_path
        if self.conference.voctoweb_thumbpath:
            props['Publishing.Voctoweb.Thumbpath'] = self.conference.voctoweb_thumbpath

        if self.conference.voctoweb_slug:
            props['Publishing.Voctoweb.Slug'] = self.conference.voctoweb_slug
        else:
            props['Publishing.Voctoweb.Slug'] = self.conference.slug

        if self.conference.youtube_token:
            props['Publishing.YouTube.Enable'] = 'yes'
            props['Publishing.YouTube.Token'] = self.conference.youtube_token
            props['Publishing.YouTube.Tags'] = "%s, %s, %s" % (self.conference.title, self.conference.slug, self.title)
            if self.conference.youtube_playlist:
                props['Publishing.YouTube.Playlists'] = self.conference.youtube_playlist
        else:
            props['Publishing.YouTube.Enable'] = 'no'

        # Fahrplan
        props['Fahrplan.Abstract'] = self.abstract.replace("\r", "")
        props['Fahrplan.Description'] = self.description.replace("\r", "")
        props['Fahrplan.DateTime'] = self.date.strftime('%Y-%m-%dT%H:%M:00+00:00')
        #props['Fahrplan.Day'] = 
        #props['Fahrplan.Duration'] = 
        props['Fahrplan.GUID'] = str(self.guid)
        props['Fahrplan.Language'] = self.language
        props['Fahrplan.Persons'] = ', '.join([pname.strip().replace(',', '') for pname in self.persons.splitlines()])
        #props['Fahrplan.Recording.Optout'] = "0"
        props['Fahrplan.Room'] = self.room if self.room else "Unknown"
        if self.track:
            props['Fahrplan.Track'] = self.track
        props['Fahrplan.Slug'] = self.slug
        props['Fahrplan.Type'] = 'lecture'
        if self.url:
            props['Fahrplan.URL'] = self.url

        props['Fahrplan.VideoDownloadURL'] = self.video_url()

        c3tt.create_meta_ticket(self.conference.tracker_project_id, self.title, self.talkid, props)['id']
        self.published = True
        self.save()

    def save(self, *args, **kwargs):
        self.slug = ("%s-%d-%s" % (self.conference.slug, self.talkid, slugify(self.title)))[:40].strip('-')
        super(Event, self).save(*args, **kwargs)

    def upload_path(self, filename):
        ext = filename[::-1].split('.', 1)[0][::-1]
        path = "videos/%s.%s" % (uuid.uuid4(), ext)
        return path
    videofile = models.FileField(max_length=1000, upload_to=upload_path, blank=True)
    remotevideofile = models.URLField(max_length=200, blank=True)

    def video_url(self):
        if self.remotevideofile:
            return self.remotevideofile
        elif self.videofile:
            return 'https://import.c3voc.de/%s' % self.videofile # TODO: dynamic domain?
        else:
            return None

    def __str__(self):
        return "%d: %s" % (self.talkid, self.title)

