"""

"""

"""
websocket - WebSocket client library for Python

Copyright (C) 2010 Hiroki Ohtani(liris)

    This library is free software; you can redistribute it and/or
    modify it under the terms of the GNU Lesser General Public
    License as published by the Free Software Foundation; either
    version 2.1 of the License, or (at your option) any later version.

    This library is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
    Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public
    License along with this library; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301  USA

"""
import http.cookies


class SimpleCookieJar(object):
    def __init__(self):
        self.jar = dict()

    def add(self, set_cookie):
        if set_cookie:
            simpleCookie = http.cookies.SimpleCookie(set_cookie)

            for k, v in simpleCookie.items():
                domain = v.get("domain")
                if domain:
                    if not domain.startswith("."):
                        domain = "." + domain
                    cookie = self.jar.get(domain) if self.jar.get(domain) else http.cookies.SimpleCookie()
                    cookie.update(simpleCookie)
                    self.jar[domain.lower()] = cookie

    def set(self, set_cookie):
        if set_cookie:
            simpleCookie = http.cookies.SimpleCookie(set_cookie)

            for k, v in simpleCookie.items():
                domain = v.get("domain")
                if domain:
                    if not domain.startswith("."):
                        domain = "." + domain
                    self.jar[domain.lower()] = simpleCookie

    def get(self, host):
        if not host:
            return ""

        cookies = []
        for domain, simpleCookie in self.jar.items():
            host = host.lower()
            if host.endswith(domain) or host == domain[1:]:
                cookies.append(self.jar.get(domain))

        return "; ".join(filter(
            None, sorted(
                ["%s=%s" % (k, v.value) for cookie in filter(None, cookies) for k, v in cookie.items()]
            )))
