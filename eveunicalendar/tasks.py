"""Tasks."""

import logging
import time

import requests
from celery import shared_task

from django.conf import settings

from .models import Event

logger = logging.getLogger(__name__)

BASE_URL = "https://discord.com/api/v10"

HEADERS = {
    "Authorization": f"Bot {getattr(settings, 'DISCORD_BOT_TOKEN')}",
    "Content-Type": "application/json",
}


def handle_rate_limit(response):
    """Handle rate limiting by checking the Retry-After header."""
    if response.status_code == 429:
        retry_after = float(
            response.headers.get("Retry-After", 1)
        )  # Default to 1 second if not provided
        logger.debug(f"Rate limited. Retrying after {retry_after} seconds...")
        time.sleep(retry_after)
        return True
    return False


def fetch_scheduled_events(guild_id):
    """Fetch all scheduled events for the guild."""
    url = f"{BASE_URL}/guilds/{guild_id}/scheduled-events"
    while True:
        response = requests.get(url, headers=HEADERS)
        if handle_rate_limit(response):
            continue
        if response.status_code == 200:
            return response.json()
        else:
            logger.debug(
                f"Error fetching events: {response.status_code} - {response.text}"
            )
            return []


def fetch_guild_member_display_name(guild_id, user_id):
    """Fetch the display name of a user within a guild."""
    url = f"{BASE_URL}/guilds/{guild_id}/members/{user_id}"
    while True:
        response = requests.get(url, headers=HEADERS)
        if handle_rate_limit(response):
            continue
        if response.status_code == 200:
            member_data = response.json()
            # Try to return the display name (nickname) or fallback to the global username
            return member_data.get("nick") or member_data["user"].get("username")
        else:
            logger.debug(
                f"Error fetching member display name for user {user_id} in guild {guild_id}: {response.status_code} - {response.text}"
            )
            return None


@shared_task
def populate_events():
    """
    Populate events from Discord
    """

    logger.debug("Fetching scheduled events...")
    events = fetch_scheduled_events(getattr(settings, "DISCORD_GUILD_ID"))

    if not events:
        logger.debug("No scheduled events found.")
        return

    # Extract the IDs of events from the Discord API
    discord_event_ids = {event["id"] for event in events}

    # Delete events that no longer exist in the latest pull
    Event.objects.exclude(eventid__in=discord_event_ids).delete()

    for event in events:
        creator_id = event.get("creator", {}).get("id")
        creator_display_name = None
        if creator_id:
            creator_display_name = fetch_guild_member_display_name(
                getattr(settings, "DISCORD_GUILD_ID"), creator_id
            )

        event_data = {
            "title": event.get("name"),
            "description": event.get("description"),
            "start_time": event.get("scheduled_start_time"),
            "end_time": event.get("scheduled_end_time"),
            "creator_global_name": creator_display_name
            or event.get("creator", {}).get("global_name"),
            "all_day": False,
        }

        # Update or create the event based on `eventid`
        obj, created = Event.objects.update_or_create(
            eventid=event.get("id"), defaults=event_data
        )

        if created:
            logger.debug(f"Created new event: {obj.title}")
        else:
            logger.debug(f"Updated existing event: {obj.title}")

    logger.debug("Event synchronization complete.")
