# Generated by Django 2.2.17 on 2021-01-14 05:16

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0009_auto_20210114_0616'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conference',
            name='owner',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
    ]
