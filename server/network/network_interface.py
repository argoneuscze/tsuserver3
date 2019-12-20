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


class NetworkInterface:
    """ An interface so that clients don't have direct access to the network.

    This could definitely be written better - e.g. abstract away all the different commands
    a client can send, and support different protocols via inheritance, but it will do for now.
    <TODO>
    """

    def __init__(self, transport):
        self.transport = transport

    def disconnect(self):
        self.transport.close()

    def send_raw_message(self, message):
        print("SND: {}".format(message))  # TODO debug
        self.transport.write(message.encode("utf-8"))

    def get_ip(self):
        return self.transport.get_extra_info("peername")[0]
