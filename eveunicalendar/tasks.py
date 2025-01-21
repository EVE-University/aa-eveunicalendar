"""Tasks."""

import logging
import time
from datetime import timedelta

import requests
from celery import shared_task
from dateutil import parser
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

from django.conf import settings
from django.utils.timezone import now

from .app_settings import (
    GOOGLE_ACTIVE_SHEET,
    GOOGLE_ARCHIVE_SHEET,
    GOOGLE_CREDENTIALS_FILE,
    GOOGLE_SHEET_ID,
)
from .models import Event
from .utils import build_events

logger = logging.getLogger(__name__)

BASE_URL = "https://discord.com/api/v10"

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

HEADERS = {
    "Authorization": f"Bot {getattr(settings, 'DISCORD_BOT_TOKEN')}",
    "Content-Type": "application/json",
}


def archive_event(event, sheet):
    sheet.values().append(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=GOOGLE_ARCHIVE_SHEET,
        valueInputOption="RAW",
        body={"values": [event]},
    ).execute()


def update_google_sheet():
    """
    Updates a Google Sheet with event data. Archives old events weekly.
    """
    if not GOOGLE_CREDENTIALS_FILE or not GOOGLE_SHEET_ID:
        return None

    end_date = now() + timedelta(days=7)

    # Query the Event model for all events
    events = Event.objects.all()

    event_list = build_events(events, end_date)

    try:
        credentials = Credentials.from_service_account_file(
            GOOGLE_CREDENTIALS_FILE, scopes=SCOPES
        )
        service = build("sheets", "v4", credentials=credentials)
    except Exception as e:
        logger.error(f"Error initializing Google Sheets API: {e}")
        return

    sheet = service.spreadsheets()

    # Get existing data from the sheet
    result = (
        sheet.values()
        .get(spreadsheetId=GOOGLE_SHEET_ID, range=GOOGLE_ACTIVE_SHEET)
        .execute()
    )
    rows = result.get("values", [])
    existing_data = {
        row[0]: row for row in rows[1:]
    }  # Create a dict with ID as the key

    # Prepare data for bulk update
    # Start with headers
    sheet_data = [["ID", "Title", "Start", "End", "Description", "Creator"]]

    # Convert existing_data to a set of IDs for quick lookup
    existing_ids = set(existing_data.keys())

    # Add or update rows based on current events
    for event in event_list:
        row = [
            event["id"],
            event["title"],
            event["start"],
            event["end"],
            event["description"],
            event["creator"],
        ]
        sheet_data.append(row)
        # Remove the matched event ID from existing_ids
        existing_ids.discard(event["id"])

    # Any IDs left in existing_ids are no longer in event_list (to be logged as removed or archived)
    for id in existing_ids:
        # Check is event has passed
        if parser.isoparse(existing_data[id][2]) < now():
            logger.info(f"Archive event: {id}")
            archive_event(existing_data[id], sheet)
        else:
            logger.info(f"Removed event: {id}")
        sheet_data.append(["", "", "", "", "", ""])

    # Bulk update the entire sheet (overwrite existing data)
    sheet.values().update(
        spreadsheetId=GOOGLE_SHEET_ID,
        range=GOOGLE_ACTIVE_SHEET,
        valueInputOption="RAW",
        body={"values": sheet_data},
    ).execute()


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
            return member_data.get("nick") or member_data["user"].get("global_name")
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
            "recurrence_rule": event.get("recurrence_rule"),
        }

        # Update or create the event based on `eventid`
        obj, created = Event.objects.update_or_create(
            eventid=event.get("id"), defaults=event_data
        )

        if created:
            logger.debug(f"Created new event: {obj.title}")
        else:
            logger.debug(f"Updated existing event: {obj.title}")

    # Push events to Google Sheets
    update_google_sheet()

    logger.debug("Event synchronization complete.")
