# coding=utf-8

from flask import Blueprint
from flask_restful import Api

from .system import System
from .searches import Searches
from .account import SystemAccount
from .tasks import SystemTasks
from .logs import SystemLogs
from .status import SystemStatus
from .health import SystemHealth
from .releases import SystemReleases
from .settings import SystemSettings
from .languages import Languages
from .languages_profiles import LanguagesProfiles
from .notifications import Notifications

api_bp_system = Blueprint('api_system', __name__)
api = Api(api_bp_system)

api.add_resource(System, '/system')
api.add_resource(Searches, '/system/searches')
api.add_resource(SystemAccount, '/system/account')
api.add_resource(SystemTasks, '/system/tasks')
api.add_resource(SystemLogs, '/system/logs')
api.add_resource(SystemStatus, '/system/status')
api.add_resource(SystemHealth, '/system/health')
api.add_resource(SystemReleases, '/system/releases')
api.add_resource(SystemSettings, '/system/settings')
api.add_resource(Languages, '/system/languages')
api.add_resource(LanguagesProfiles, '/system/languages/profiles')
api.add_resource(Notifications, '/system/notifications')
