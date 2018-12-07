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

from server.util.exceptions import AreaError


class Area:
    def __init__(self, area_id, server, name, background, bg_lock):
        self.clients = set()
        self.id = area_id
        self.name = name
        self.background = background
        self.bg_lock = bg_lock
        self.server = server
        self.music_looper = None
        self.next_message_time = 0
        self.hp_def = 10
        self.hp_pro = 10
        self.doc = 'No document.'
        self.status = 'IDLE'
        self.judgelog = []
        self.current_music = ''
        self.current_music_player = ''

    def new_client(self, client):
        self.clients.add(client)

    def remove_client(self, client):
        self.clients.remove(client)

    def is_char_available(self, char_id):
        return char_id not in [x.char_id for x in self.clients]

    def get_rand_avail_char_id(self):
        avail_set = set(range(len(self.server.char_list))) - set([x.char_id for x in self.clients])
        if len(avail_set) == 0:
            raise AreaError('No available characters.')
        return random.choice(tuple(avail_set))

    def send_command(self, cmd, *args):
        for c in self.clients:
            c.send_command(cmd, *args)

    def send_host_message(self, msg):
        self.send_command('CT', self.server.config['hostname'], msg)

    def set_next_msg_delay(self, msg_length):
        delay = min(3000, 100 + 60 * msg_length)
        self.next_message_time = round(time.time() * 1000.0 + delay)

    def play_music(self, name, cid, length=-1):
        self.send_command('MC', name, cid)
        if self.music_looper:
            self.music_looper.cancel()
        if length > 0:
            self.music_looper = asyncio.get_event_loop().call_later(length,
                                                                    lambda: self.play_music(name, -1, length))

    def get_target_by_char_name(self, char_name):
        for c in self.clients:
            if c.get_char_name() == char_name:
                return c
        return None

    def can_send_message(self):
        return (time.time() * 1000.0 - self.next_message_time) > 0

    def change_hp(self, side, val):
        if not 0 <= val <= 10:
            raise AreaError('Invalid penalty value.')
        if not 1 <= side <= 2:
            raise AreaError('Invalid penalty side.')
        if side == 1:
            self.hp_def = val
        elif side == 2:
            self.hp_pro = val
        self.send_command('HP', side, val)

    def change_background(self, bg):
        if bg not in self.server.backgrounds:
            raise AreaError('Invalid background name.')
        self.background = bg
        self.send_command('BN', self.background)

    def change_status(self, value):
        allowed_values = ('idle', 'building-open', 'building-full', 'casing-open', 'casing-full', 'recess')
        if value.lower() not in allowed_values:
            raise AreaError('Invalid status. Possible values: {}'.format(', '.join(allowed_values)))
        self.status = value.upper()

    def change_doc(self, doc='No document.'):
        self.doc = doc

    def add_to_judgelog(self, client, msg):
        if len(self.judgelog) >= 10:
            self.judgelog = self.judgelog[1:]
        self.judgelog.append('{} ({}) {}.'.format(client.get_char_name(), client.get_ip(), msg))

    def add_music_playing(self, client, name):
        self.current_music_player = client.get_char_name()
        self.current_music = name
