"""App settings."""

from django.conf import settings

GOOGLE_CREDENTIALS_FILE = getattr(settings, "GOOGLE_CREDENTIALS_FILE", None)
GOOGLE_SHEET_ID = getattr(settings, "GOOGLE_SHEET_ID", None)
GOOGLE_ACTIVE_SHEET = getattr(settings, "GOOGLE_ACTIVE_SHEET", "Current")
GOOGLE_ARCHIVE_SHEET = getattr(settings, "GOOGLE_ARCHIVE_SHEET", "Archive")
