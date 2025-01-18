from django.utils.translation import gettext_lazy as _

from allianceauth import hooks
from allianceauth.services.hooks import MenuItemHook, UrlHook

from . import urls


class EunicalendarMenuItem(MenuItemHook):
    """This class ensures only authorized users will see the menu entry"""

    def __init__(self):
        # setup menu entry for sidebar
        MenuItemHook.__init__(
            self,
            _("EveUniCalendar"),
            "fas fa-calendar-days fa-fw",
            "eveunicalendar:index",
            navactive=["eveunicalendar:"],
        )

    def render(self, request):
        if request.user.has_perm("eveunicalendar.basic_access"):
            return MenuItemHook.render(self, request)
        return ""


@hooks.register("menu_item_hook")
def register_menu():
    return EunicalendarMenuItem()


@hooks.register("url_hook")
def register_urls():
    return UrlHook(urls, "eveunicalendar", r"^eveunicalendar/")
