# Generated by Django 3.1.5 on 2021-01-14 02:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0006_auto_20210114_0202'),
    ]

    operations = [
        migrations.RenameField(
            model_name='conference',
            old_name='name',
            new_name='title',
        ),
    ]
