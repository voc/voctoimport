from django.shortcuts import render, redirect, get_object_or_404
from .models import Conference, Event
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponse, JsonResponse
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
from .forms import EventForm
from django.utils.dateparse import parse_datetime
import datetime
import json
import time
import uuid
from django.utils import timezone
tz = timezone.get_default_timezone()

@login_required
def view_index(request):
    if request.user.is_superuser:
        conferences = Conference.objects.all()
    else:
        conferences = Conference.objects.filter(admins__in=[request.user])
    return render(request, "event/index.html", {'conferences': conferences})

@login_required
def view_conference(request, cslug):
    if request.user.is_superuser:
        conference = get_object_or_404(Conference, slug=cslug)
    else:
        conference = get_object_or_404(Conference, slug=cslug, admins__in=[request.user])

    events = conference.event_set.all().order_by('-date')
    return render(request, "event/conference.html", {'conference': conference, 'events': events})

@login_required
def view_event(request, cslug, eguid):
    if request.user.is_superuser:
        conference = get_object_or_404(Conference, slug=cslug)
    else:
        conference = get_object_or_404(Conference, slug=cslug, admins__in=[request.user])

    event = get_object_or_404(Event, conference=conference, guid=eguid)

    if request.method == "POST":
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            event = form.save(commit=False)
            event.date = parse_datetime('%sT%s:00' % (form.cleaned_data['date_date'], form.cleaned_data['date_time']))
            event.save()
            if 'submit' in request.POST and event.video_url():
                event.publish()
            return redirect("/conference/%s" % (conference.slug))
    else:
        form = EventForm(instance=event)
    return render(request, "event/eventform.html", {'conference': conference, 'form': form, 'readonly': event.published})

@login_required
def view_new_event(request, cslug):
    if request.user.is_superuser:
        conference = get_object_or_404(Conference, slug=cslug)
    else:
        conference = get_object_or_404(Conference, slug=cslug, admins__in=[request.user])

    if request.method == "POST":
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.conference = conference
            event.date = parse_datetime('%sT%s:00' % (form.cleaned_data['date_date'], form.cleaned_data['date_time']))
            event.save()
            return redirect("/conference/%s" % (conference.slug))
    else:
        lasttalk = Event.objects.filter(conference=conference).order_by('-talkid').first()
        if lasttalk is not None:
            form = EventForm(initial={'room': lasttalk.room, 'language': lasttalk.language})
        else:
            form = EventForm()
    return render(request, "event/eventform.html", {'conference': conference, 'form': form})

def scheduledict(cslug, request):
    conference = get_object_or_404(Conference, slug=cslug)

    schedule = {}
    schedule['version'] = str(int(time.time()))
    schedule['conference'] = {}
    schedule['conference']['acronym'] = conference.slug
    schedule['conference']['title'] = conference.title
    schedule['conference']['time_zone_name'] = 'Europe/Berlin'
    rooms = {}
    schedule['rooms'] = rooms
    persons = []
    schedule['days'] = []
    days = {}
    for dbevent in conference.event_set.order_by('date').all():
        if not dbevent.video_url() and request.GET.get("showall") != "yes":
            continue
        date = dbevent.date.astimezone(tz).strftime("%Y-%m-%d")
        if date not in days:
            days[date] = {}
            dayinfo = {}
            dayinfo['date'] = date
            dayinfo['rooms'] = days[date]
            schedule['days'].append(dayinfo)
        room = dbevent.room if dbevent.room else 'None'
        if room not in days[date]:
            days[date][room] = []
        if room not in rooms:
            rooms[room] = uuid.uuid5(uuid.NAMESPACE_URL, f'https://import.c3voc.de/conference{cslug}/room/{room}')
        event = {}
        event['guid'] = str(dbevent.guid)
        event['type'] = 'lecture'
        event['id'] = dbevent.talkid
        event['slug'] = dbevent.slug
        event['title'] = dbevent.title
        event['subtitle'] = ''
        tzoffset = dbevent.date.astimezone(tz).strftime('%z')
        if tzoffset == "":
            tzoffset = "+0000"
        event['date'] = dbevent.date.astimezone(tz).strftime('%%Y-%%m-%%dT%%H:%%M:00%s:%s' % (tzoffset[:3], tzoffset[3:]))
        event['start'] = dbevent.date.astimezone(tz).strftime('%H:%M')
        event['duration'] = dbevent.duration
        event['room'] = room
        event['track'] = dbevent.track if dbevent.track else ''
        event['language'] = dbevent.language
        event['logo'] = ''
        event['abstract'] = dbevent.abstract
        event['description'] = dbevent.description
        event['recording'] = {'optout': False}
        event['persons'] = []
        event['url'] = dbevent.url if dbevent.url else ''
        if dbevent.video_url():
            event['recording']['url'] = dbevent.video_url()
            event['video_download_url'] = dbevent.video_url()
        for name in dbevent.persons.strip().splitlines():
            name = name.strip()
            if name not in persons:
                persons.append(name)
            event['persons'].append({'id': persons.index(name)+1, 'public_name': name})
        days[date][room].append(event)

    return schedule

# schedule/<cslug>.json
def view_schedulejson(request, cslug):
    schedule = scheduledict(cslug, request)
    index = 1
    return HttpResponse(json.dumps({
        "$schema": "https://c3voc.de/schedule/schema.json",
        "schedule": {
            "generator": {"name": "voctoimport", "version": "0.2"},
            "conference": {
                **schedule['conference'],
                "rooms": [
                    {"name": name, "guid": str(guid)} for name, guid in schedule['rooms'].items()
                ],
                "days": [{
                    "index": i+1,
                    **day
                } for i, day in enumerate(schedule['days'])]
            }
        }
    }, indent=2),content_type='application/json' )

def view_schedulexml(request, cslug):
    schedule = scheduledict(cslug, request)

    schedulexml = Element('schedule')
    schedulexml.set("{http://www.w3.org/2001/XMLSchema-instance}noNamespaceSchemaLocation", "https://c3voc.de/schedule/schema.xsd")

    SubElement(schedulexml, 'generator', name='voctoimport', version='0.2')

    version = SubElement(schedulexml, 'version')
    version.text=str(int(time.time()))

    conference = SubElement(schedulexml, 'conference')
    for key, value in schedule['conference'].items():
        xmlobj = SubElement(conference, key)
        xmlobj.text = str(value)

    for i, sday in enumerate(schedule['days']):
        day = SubElement(schedulexml, 'day', date=sday['date'], index=str(i+1))
        for rname, revents in sday['rooms'].items():
            # TODO: Add room guid
            room = SubElement(day, 'room', name=rname, guid=str(schedule['rooms'][rname]))

            for event in revents:
                xmlevent = SubElement(room, 'event', guid=str(event['guid']), id=str(event['id']))

                for key, value in event.items():
                    if key in ['persons', 'id', 'guid', 'recording']:
                        continue
                    xmlobj = SubElement(xmlevent, key)
                    xmlobj.text = str(value)

                xmlrecording = SubElement(xmlevent, 'recording')
                xmloptout = SubElement(xmlrecording, 'optout')
                xmloptout.text = 'false'
                SubElement(xmlrecording, 'license')

                xmlpersons = SubElement(xmlevent, 'persons')
                for person in event['persons']:
                    xmlperson = SubElement(xmlpersons, 'person', id=str(person['id']))
                    xmlperson.text = person['public_name']

    return HttpResponse(b"<?xml version='1.0' encoding='utf-8' ?>\n" + ElementTree.tostring(schedulexml), content_type='application/xml')
