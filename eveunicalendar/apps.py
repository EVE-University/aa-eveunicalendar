from django.apps import AppConfig

from eveunicalendar import __version__


class EunicalendarConfig(AppConfig):
    name = "eveunicalendar"
    label = "eveunicalendar"
    verbose_name = "aa-eveunicalendar V" + __version__

    def ready(self):
        import eveunicalendar.signals  # noqa: F401
