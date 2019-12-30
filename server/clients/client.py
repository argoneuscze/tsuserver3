# tsuserver3, an Attorney Online server
#
# Copyright (C) 2018 argoneus <argoneuscze@gmail.com>
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
from server.util import logger
from server.util.attributes import set_dict_attribute, get_dict_attribute
from server.util.exceptions import ClientError, AreaError


def default_attributes():
    return {
        "is_moderator": False,
        "ic": {"position": "", "muted": False},
        "ooc": {"name": None},
        "global": {"muted": False},
        "adverts": {"muted": False},
    }


class Client:
    def __init__(self, server, network, user_id, area):
        self.network = network
        self.hdid = ""
        self.id = user_id
        self.char_id = -1
        self.area = area
        self.server = server
        self.software = None
        self._attributes = default_attributes()

    def _send_raw_message(self, msg):
        if self.server.config["debug"]:
            print(logger.log_debug(f"[SND]{msg}", self))
        self.network.send_raw_message(msg)

    def send_command(self, command, *args):
        if args:
            self._send_raw_message(
                "{}#{}#%".format(command, "#".join([str(x) for x in args]))
            )
        else:
            self._send_raw_message("{}#%".format(command))

    def send_host_message(self, msg):
        self.send_command("CT", self.server.config["hostname"], msg)

    def send_motd(self):
        self.send_host_message(
            "=== MOTD ===\r\n{}\r\n=============".format(self.server.config["motd"])
        )

    def set_attr(self, attr_path, value):
        set_dict_attribute(self._attributes, attr_path, value)

    def get_attr(self, attr_path):
        return get_dict_attribute(self._attributes, attr_path)

    def disconnect(self):
        self.network.disconnect()

    def change_character(self, char_id, force=False):
        if not self.server.is_valid_char_id(char_id):
            raise ClientError("Invalid Character ID.")
        if not force and not self.area.is_char_available(char_id):
            raise ClientError("Character not available.")
        old_char = self.get_char_name()
        self.char_id = char_id
        self.send_command("PV", self.id, "CID", self.char_id)
        logger.log_server(
            "[{}]Changed character from {} to {}.".format(
                self.area.id, old_char, self.get_char_name()
            ),
            self,
        )

    def reload_character(self):
        try:
            self.change_character(self.char_id, True)
        except ClientError:
            raise

    def change_area(self, area):
        if self.software != "AOClassic":
            raise ClientError("To change areas, you must use the AO Classic client.")
        if self.area == area:
            raise ClientError("You are already in this area.")
        old_area = self.area
        if not area.is_char_available(self.char_id):
            try:
                new_char_id = area.get_rand_avail_char_id()
            except AreaError:
                raise ClientError("No available characters in that area.")
            self.area.remove_client(self)
            self.area = area
            area.new_client(self)
            self.change_character(new_char_id)
            self.send_host_message(
                "Character taken, switched to {}.".format(self.get_char_name())
            )
        else:
            self.area.remove_client(self)
            self.area = area
            area.new_client(self)
        self.send_host_message("Changed area to {}.".format(area.name))
        logger.log_server(
            "[{}]Changed area from {} ({}) to {} ({}).".format(
                self.get_char_name(),
                old_area.name,
                old_area.id,
                self.area.name,
                self.area.id,
            ),
            self,
        )

        self.send_command("HP", 1, self.area.get_attr("health.defense"))
        self.send_command("HP", 2, self.area.get_attr("health.prosecution"))
        self.send_command("BN", self.area.get_attr("background.name"))
        self.send_evidence_list()
        self.server.send_arup_players()

    def get_area_info(self, area_id):
        info = ""
        try:
            area = self.server.area_manager.get_area_by_id(area_id)
        except AreaError:
            raise
        info += "= Area {}: {} ==".format(area.id, area.name)
        sorted_clients = sorted(area.clients, key=lambda x: x.get_char_name())
        for c in sorted_clients:
            info += "\r\n{}".format(c.get_char_name())
            if self.get_attr("is_moderator"):
                info += " ({})".format(c.get_ip())
        return info

    def send_area_info(self, area_id):
        try:
            info = self.get_area_info(area_id)
        except AreaError:
            raise
        self.send_host_message(info)

    def send_all_area_info(self):
        info = "== Area List =="
        for i in range(len(self.server.area_manager.areas)):
            info += "\r\n{}".format(self.get_area_info(i))
        self.send_host_message(info)

    def send_evidence_list(self):
        evi_list = self.area.evidence_manager.get_evidence_list()
        evi_packet = ["&".join(x) for x in evi_list]
        self.send_command("LE", *evi_packet)

    def send_done(self):
        avail_char_ids = set(range(len(self.server.char_list))) - set(
            [x.char_id for x in self.area.clients]
        )
        char_list = [-1] * len(self.server.char_list)
        for x in avail_char_ids:
            char_list[x] = 0
        self.send_command("CharsCheck", *char_list)
        self.send_command("HP", 1, self.area.get_attr("health.defense"))
        self.send_command("HP", 2, self.area.get_attr("health.prosecution"))
        self.send_command("BN", self.area.get_attr("background.name"))
        self.send_command("MM", 1)
        self.send_evidence_list()

        self.send_command("DONE")

    def char_select(self):
        self.char_id = -1
        self.send_done()

    def auth_mod(self, password):
        if self.get_attr("is_moderator"):
            raise ClientError("Already logged in.")
        if password == self.server.config["modpass"]:
            self.set_attr("is_moderator", True)
        else:
            raise ClientError("Invalid password.")

    def get_ip(self):
        return self.network.get_ip()

    def get_char_name(self):
        if self.char_id == -1:
            return "CHAR_SELECT"
        return self.server.char_list[self.char_id]

    def change_position(self, pos=""):
        if pos not in ("", "def", "pro", "hld", "hlp", "jud", "wit"):
            raise ClientError(
                "Invalid position. Possible values: def, pro, hld, hlp, jud, wit."
            )
        self.set_attr("ic.position", pos)
