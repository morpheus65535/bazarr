from plex.core.idict import idict
from plex.interfaces.core.base import Interface


class PluginPreferencesInterface(Interface):
    path = ':/plugins/*/prefs'

    def get(self, plugin_id, id=None):
        response = self.http.get('/:/plugins/%s/prefs' % plugin_id)

        container = self.parse(response, idict({
            'MediaContainer': ('MediaContainer', idict({
                'Setting': 'Setting'
            }))
        }))

        if container is None or id is None:
            return container

        for setting in container:
            if setting.id == id:
                return setting

        return None

    def set(self, plugin_id, id, value):
        response = self.http.get('/:/plugins/%s/prefs/set' % plugin_id, query={
            id: self.to_setting_value(value, type(value))
        })

        return response.status_code == 200

    def to_setting_value(self, value, value_type=None):
        if value is None:
            return None

        if value_type is bool:
            return str(value).lower()

        return str(value)
