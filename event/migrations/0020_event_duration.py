# Generated by Django 2.2.19 on 2021-04-19 22:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('event', '0019_auto_20210412_0000'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='duration',
            field=models.CharField(default='01:00', max_length=5),
        ),
    ]
