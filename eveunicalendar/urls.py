"""Routes."""

from django.urls import path

from . import views

app_name = "eveunicalendar"

urlpatterns = [
    path("", views.index, name="index"),
    path("private-events/", views.private_events, name="private_events"),
]
