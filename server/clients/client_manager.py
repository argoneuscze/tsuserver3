# tsuserver3, an Attorney Online server
#
# Copyright (C) 2016 argoneus <argoneuscze@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from server.clients.client import Client


class ClientManager:
    def __init__(self, server):
        self.clients = set()
        self.cur_id = 0
        self.server = server

    def new_client(self, network, area):
        c = Client(self.server, network, self.cur_id, area)
        self.clients.add(c)
        self.cur_id += 1
        return c

    def remove_client(self, client):
        self.clients.remove(client)

    def get_targets_by_ip(self, ip):
        clients = []
        for client in self.clients:
            if client.get_ip() == ip:
                clients.append(client)
        return clients

    def get_targets_by_ooc_name(self, name):
        clients = []
        for client in self.clients:
            if client.name == name:
                clients.append(client)
        return clients

    def get_targets(self, client, target):
        # check if it's IP but only if mod
        if client.is_mod:
            clients = self.get_targets_by_ip(target)
            if clients:
                return clients
        # check if it's a character name in the same area
        c = client.area.get_target_by_char_name(target)
        if c:
            return [c]
        # check if it's an OOC name
        ooc = self.get_targets_by_ooc_name(target)
        if ooc:
            return ooc
        return None
