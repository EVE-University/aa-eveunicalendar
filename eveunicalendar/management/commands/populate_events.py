from django.core.management.base import BaseCommand

from eveunicalendar.tasks import populate_events


class Command(BaseCommand):
    help = "Synchronize events from Discord and update Google Sheets"

    def handle(self, *args, **options):
        self.stdout.write("Starting event synchronization...")
        try:
            populate_events()
            self.stdout.write(
                self.style.SUCCESS("Event synchronization completed successfully.")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"An error occurred: {e}"))
