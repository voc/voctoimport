# Generated by Django 3.1.5 on 2021-01-14 02:01

from django.db import migrations, models
import event.models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0004_event_title'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='videofile',
            field=models.FileField(blank=True, upload_to=event.models.Event.upload_path),
        ),
    ]