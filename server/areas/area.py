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

import asyncio
import random
import time

from server.areas.evidence_manager import EvidenceManager
from server.util.attributes import set_dict_attribute, get_dict_attribute
from server.util.exceptions import AreaError


def default_attributes(name, background, bg_lock, is_casing):
    return {
        "name": name,
        "status": "IDLE" if is_casing else "NOCASE",
        "is_casing": is_casing,
        "background": {"name": background, "locked": bg_lock},
        "health": {"defense": 10, "prosecution": 10},
        "case": {"master": "None", "document": "None"},
    }


class Area:
    def __init__(self, area_id, server, name, background, bg_lock, is_casing):
        self.clients = set()
        self.id = area_id
        self.name = name
        self.server = server
        self.evidence_manager = EvidenceManager()
        self.music_looper = None
        self.next_message_time = 0
        self._attributes = default_attributes(name, background, bg_lock, is_casing)

    def new_client(self, client):
        self.clients.add(client)

    def remove_client(self, client):
        self.clients.remove(client)

    def set_attr(self, attr_path, value):
        set_dict_attribute(self._attributes, attr_path, value)

    def get_attr(self, attr_path):
        return get_dict_attribute(self._attributes, attr_path)

    def is_char_available(self, char_id):
        return char_id not in [x.char_id for x in self.clients]

    def get_rand_avail_char_id(self):
        avail_set = set(range(len(self.server.char_list))) - set(
            [x.char_id for x in self.clients]
        )
        if len(avail_set) == 0:
            raise AreaError("No available characters.")
        return random.choice(tuple(avail_set))

    def send_command(self, cmd, *args):
        for c in self.clients:
            c.send_command(cmd, *args)

    def send_host_message(self, msg):
        self.send_command("CT", self.server.config["hostname"], msg)

    def send_evidence_list(self):
        evi_list = self.evidence_manager.get_evidence_list()
        evi_packet = ["&".join(x) for x in evi_list]
        for c in self.clients:
            c.send_command("LE", *evi_packet)

    def set_next_msg_delay(self, msg_length):
        delay = min(3000, 100 + 50 * msg_length)
        self.next_message_time = round(time.time() * 1000.0 + delay)

    def play_music(self, name, cid, length=-1):
        self.send_command("MC", name, cid)
        if self.music_looper:
            self.music_looper.cancel()
        if length > 0:
            self.music_looper = asyncio.get_event_loop().call_later(
                length, lambda: self.play_music(name, -1, length)
            )

    def get_target_by_char_name(self, char_name):
        for c in self.clients:
            if c.get_char_name() == char_name:
                return c
        return None

    def can_send_message(self):
        return (time.time() * 1000.0 - self.next_message_time) > 0

    def change_hp(self, side, val):
        if not 0 <= val <= 10:
            raise AreaError("Invalid penalty value.")
        if not 1 <= side <= 2:
            raise AreaError("Invalid penalty side.")
        if side == 1:
            self.set_attr("health.defense", val)
        elif side == 2:
            self.set_attr("health.prosecution", val)
        self.send_command("HP", side, val)

    def change_background(self, bg):
        if bg not in self.server.backgrounds:
            raise AreaError("Invalid background name.")
        self.set_attr("background.name", bg)
        self.send_command("BN", bg)

    def change_status(self, value):
        allowed_values = (
            "idle",
            "building",
            "casing",
            "recess",
        )
        if value.lower() not in allowed_values:
            raise AreaError(
                f"Invalid status. Possible values: {', '.join(allowed_values)}"
            )
        if value == self.get_attr("status"):
            raise AreaError("This status is already set.")
        self.set_attr("status", value.upper())
        self.server.send_arup_status()

    def change_cm(self, name):
        name = name[:20]
        self.set_attr("case.master", name)
        self.server.send_arup_cm()

    def change_doc(self, url="No document."):
        self.set_attr("case.document", url)
