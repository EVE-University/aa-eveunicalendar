
# **EVE Uni Calendar Plugin for Alliance Auth**

This plugin app for Alliance Auth displays Eve University's Discord events in a calendar view, making it easy to keep track of scheduled activities.

---

## **Features**
- Displays Eve University's Discord events in a visually appealing calendar view.
- Fully integrated with Alliance Auth and leverages Discord data.
- Supports logging events to Google Sheets for historical tracking.

---

## **Installation**

1. **Add the app to `INSTALLED_APPS`:**
   Add `eveunicalendar` to the `INSTALLED_APPS` section of your `settings.py`:
   ```python
   INSTALLED_APPS += [
       'eveunicalendar',
   ]
   ```

2. **Apply migrations and collect static files:**
   Run the following commands:
   ```bash
   python manage.py migrate
   python manage.py collectstatic
   ```

---

## **Configuration**

1. **Ensure Discord integration is enabled in Alliance Auth.**

2. **Set the following environment variables in your `local.py` or `.env` file:**
   - `DISCORD_GUILD_ID`: Your Eve University Discord server ID.
   - `DISCORD_BOT_TOKEN`: A valid bot token with permission to read scheduled events.

3. **Configure Google Sheets integration:**
   Place your `credentials.json` file (from Google Sheets API setup) in the same directory as your `local.py` file, and add the following configuration to your `local.py`:
   ```python
   import os

   BASE_DIR = os.path.dirname(os.path.abspath(__file__))
   GOOGLE_CREDENTIALS_FILE = os.path.join(BASE_DIR, 'credentials.json')
   ```
**Optional config setting**

Defaults are shown when not present.
   ```python
   GOOGLE_ACTIVE_SHEET = 'Current'
   GOOGLE_ARCHIVE_SHEET = 'Archive'
   ```

---

## **Celery Integration**

Add the following task to your Celery Beat schedule to fetch events hourly:

```python
from celery.schedules import crontab

CELERYBEAT_SCHEDULE["populate_events"] = {
    "task": "eveunicalendar.tasks.populate_events",
    "schedule": crontab(minute=0),  # Runs hourly
}
```

Ensure your Celery worker and Celery Beat services are running to sync events automatically.

---

## **Support**

For questions, issues, or feature requests, please contact the Eve University development team or submit an issue on the project's repository.
