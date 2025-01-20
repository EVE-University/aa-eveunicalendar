"""Models."""

from django.db import models


class General(models.Model):
    """A meta model for app permissions."""

    class Meta:
        managed = False
        default_permissions = ()
        permissions = (("basic_access", "Can access this app"),)


class Event(models.Model):
    title = models.CharField(max_length=255)
    eventid = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    creator_global_name = models.CharField(max_length=255, blank=True, null=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    all_day = models.BooleanField(default=False)
    recurrence_rule = models.CharField(max_length=1000, blank=True, null=True)

    class Meta:
        ordering = ["start_time"]

    def __str__(self):
        return f"{self.start_time} - {self.title} (Creator: {self.creator_global_name or 'Unknown'})"
