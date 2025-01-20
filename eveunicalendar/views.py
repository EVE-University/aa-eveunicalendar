import ast
import logging
from datetime import datetime, timedelta

from dateutil import parser
from dateutil.rrule import DAILY, MONTHLY, WEEKLY, YEARLY, rrule

from django.conf import settings
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse
from django.shortcuts import render

from .models import Event

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

        event_list = []

        # Helper function to map frequency
        def get_frequency(freq):
            return {1: DAILY, 2: WEEKLY, 3: MONTHLY, 4: YEARLY}.get(freq, None)

        # Serialize events for FullCalendar
        # Process events and handle recurrence rules
        for event in events:

            # Add the original event only if it does not have a recurrence rule
            if not event.recurrence_rule:
                event_list.append(
                    {
                        "id": event.eventid,
                        "title": event.title,
                        "start": event.start_time.isoformat(),
                        "end": event.end_time.isoformat() if event.end_time else None,
                        "allDay": event.all_day,
                        "description": event.description or "No description",
                        "creator": event.creator_global_name or "Unknown",
                        "discord_link": f"discord://-/events/{getattr(settings, 'DISCORD_GUILD_ID')}/{event.eventid}",
                    }
                )

            # Handle recurring events if `recurrence_rule` is present
            else:
                try:
                    rule = ast.literal_eval(event.recurrence_rule)
                except (ValueError, SyntaxError) as e:
                    logger.error(
                        f"Invalid recurrence rule for event {event.eventid}: {e}"
                    )
                    continue

                # Parse recurrence rule details
                start_time = parser.isoparse(rule.get("start"))
                frequency = get_frequency(rule.get("frequency"))
                interval = rule.get("interval", 1)
                by_weekday = rule.get("by_weekday")
                by_month = rule.get("by_month")
                by_month_day = rule.get("by_month_day")
                by_year_day = rule.get("by_year_day")
                count = rule.get("count")
                end_time = parser.isoparse(rule["end"]) if rule.get("end") else None

                # Skip if frequency is invalid
                if not frequency:
                    continue

                # Generate recurring dates using rrule
                recurrences = rrule(
                    freq=frequency,
                    dtstart=start_time,
                    interval=interval,
                    byweekday=by_weekday,
                    bymonth=by_month,
                    bymonthday=by_month_day,
                    byyearday=by_year_day,
                    until=min(end_time, end_date) if end_time else end_date,
                    count=count,
                )

                for occurrence in recurrences:
                    event_list.append(
                        {
                            "id": f"{event.eventid}-{occurrence.isoformat()}",
                            "title": event.title,
                            "start": occurrence.isoformat(),
                            "end": (
                                (
                                    occurrence + (event.end_time - event.start_time)
                                ).isoformat()
                                if event.end_time
                                else None
                            ),
                            "allDay": event.all_day,
                            "description": event.description or "No description",
                            "creator": event.creator_global_name or "Unknown",
                            "discord_link": f"discord://-/events/{getattr(settings, 'DISCORD_GUILD_ID')}/{event.eventid}",
                        }
                    )

        return JsonResponse(event_list, safe=False)
    else:
        return JsonResponse({"error": "Invalid method"}, status=405)
