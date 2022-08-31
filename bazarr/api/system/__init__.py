# coding=utf-8

from flask_restx import Namespace

from .system import System
from .searches import Searches
from .account import SystemAccount
from .backups import SystemBackups
from .tasks import SystemTasks
from .logs import SystemLogs
from .status import SystemStatus
from .health import SystemHealth
from .releases import SystemReleases
from .settings import SystemSettings
from .languages import Languages
from .languages_profiles import LanguagesProfiles
from .notifications import Notifications

api_ns_system = Namespace('system', description='System API endpoint')

api_ns_system.add_resource(System, 'system')
api_ns_system.add_resource(Searches, 'system/searches')
api_ns_system.add_resource(SystemAccount, 'system/account')
api_ns_system.add_resource(SystemBackups, 'system/backups')
api_ns_system.add_resource(SystemTasks, 'system/tasks')
api_ns_system.add_resource(SystemLogs, 'system/logs')
api_ns_system.add_resource(SystemStatus, 'system/status')
api_ns_system.add_resource(SystemHealth, 'system/health')
api_ns_system.add_resource(SystemReleases, 'system/releases')
api_ns_system.add_resource(SystemSettings, 'system/settings')
api_ns_system.add_resource(Languages, 'system/languages')
api_ns_system.add_resource(LanguagesProfiles, 'system/languages/profiles')
api_ns_system.add_resource(Notifications, 'system/notifications')
