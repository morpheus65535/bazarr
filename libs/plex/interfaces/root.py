from plex.core.idict import idict
from plex.interfaces.core.base import Interface


class RootInterface(Interface):
    def detail(self):
        response = self.http.get()

        return self.parse(response, idict({
            'MediaContainer': ('Detail', idict({
                'Directory': 'Directory'
            }))
        }))

    def version(self):
        detail = self.detail()

        if not detail:
            return None

        return detail.version

    def clients(self):
        response = self.http.get('clients')

        return self.parse(response, idict({
            'MediaContainer': ('ClientContainer', idict({
                'Server': 'Client'
            }))
        }))

    def players(self):
        pass

    def servers(self):
        response = self.http.get('servers')

        return self.parse(response, idict({
            'MediaContainer': ('Container', idict({
                'Server': 'Server'
            }))
        }))

    def agents(self):
        response = self.http.get('system/agents')

        return self.parse(response, idict({
            'MediaContainer': ('Container', idict({
                'Agent': 'Agent'
            }))
        }))

    def primary_agent(self, guid, media_type):
        response = self.http.get('/system/agents/%s/config/%s' % (guid, media_type))
        return self.parse(response, idict({
            'MediaContainer': ('Container', idict({
                'Agent': 'Agent'
            }))
        }))
