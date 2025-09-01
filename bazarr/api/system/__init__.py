# coding=utf-8

from .system import api_ns_system
from .searches import api_ns_system_searches
from .account import api_ns_system_account
from .announcements import api_ns_system_announcements
from .backups import api_ns_system_backups
from .tasks import api_ns_system_tasks
from .logs import api_ns_system_logs
from .status import api_ns_system_status
from .health import api_ns_system_health
from .ping import api_ns_system_ping
from .releases import api_ns_system_releases
from .settings import api_ns_system_settings
from .languages import api_ns_system_languages
from .languages_profiles import api_ns_system_languages_profiles
from .notifications import api_ns_system_notifications
from .jobs import api_ns_system_jobs

api_ns_list_system = [
    api_ns_system,
    api_ns_system_account,
    api_ns_system_announcements,
    api_ns_system_backups,
    api_ns_system_health,
    api_ns_system_languages,
    api_ns_system_languages_profiles,
    api_ns_system_logs,
    api_ns_system_notifications,
    api_ns_system_ping,
    api_ns_system_releases,
    api_ns_system_searches,
    api_ns_system_settings,
    api_ns_system_status,
    api_ns_system_tasks,
    api_ns_system_jobs,
]
