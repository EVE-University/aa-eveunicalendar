"""Admin site."""

from django.contrib import admin

from .models import Event

# Register your models for the admin site here.


class EventAdmin(admin.ModelAdmin):
    list_display = ("title", "start_time", "end_time", "creator_global_name")
    list_filter = ("all_day", "creator_global_name")
    search_fields = ("title", "creator_global_name")


admin.site.register(Event, EventAdmin)
