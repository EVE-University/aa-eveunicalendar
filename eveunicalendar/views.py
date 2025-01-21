import logging
from datetime import datetime, timedelta

from dateutil import parser

from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import render

from .models import Event
from .utils import build_events

logger = logging.getLogger(__name__)


@login_required
@permission_required("eveunicalendar.basic_access")
def index(request):
    """Eve University calendar"""

    return render(
        request,
        "eveunicalendar/index.html",
        {},
    )


@login_required
@permission_required("eveunicalendar.basic_access")
def private_events(request):
    """Return events in JSON format for FullCalendar"""
    if request.method == "POST":
        # Parse start and end dates from the request (if provided by FullCalendar)
        start = request.POST.get("start")  # ISO8601 format expected
        end = request.POST.get("end")  # ISO8601 format expected

        # Convert string dates to datetime objects
        if start and end:
            start_date = parser.isoparse(start)
            end_date = parser.isoparse(end)
        else:
            # Default to a 30-day range if no dates are provided
            start_date = datetime.now() - timedelta(days=15)
            end_date = datetime.now() + timedelta(days=15)

        # Query the Event model for events within the range
        events = Event.objects.filter(
            start_time__gte=start_date,
            start_time__lte=end_date,
        )

        event_list = build_events(events, end_date)

        return JsonResponse(event_list, safe=False)
    else:
        return JsonResponse({"error": "Invalid method"}, status=405)
