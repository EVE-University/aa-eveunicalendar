# Generated by Django 4.2.17 on 2025-01-19 00:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("eveunicalendar", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="event",
            name="creator_global_name",
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
