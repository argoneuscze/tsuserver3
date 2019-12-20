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

import yaml

from server.areas.area import Area
from server.util.exceptions import AreaError


class AreaManager:
    def __init__(self, server):
        self.server = server
        self.cur_id = 0
        self.areas = []
        self.load_areas()

    def load_areas(self):
        with open("config/areas.yaml", "r") as chars:
            areas = yaml.load(chars)
        for item in areas:
            self.areas.append(
                Area(
                    self.cur_id,
                    self.server,
                    item["area"],
                    item["background"],
                    item["bglock"],
                )
            )
            self.cur_id += 1

    def get_default_area(self):
        return self.areas[0]

    def get_area_by_name(self, name):
        for area in self.areas:
            if area.name == name:
                return area
        raise AreaError("Area not found.")

    def get_area_by_id(self, num):
        for area in self.areas:
            if area.id == num:
                return area
        raise AreaError("Area not found.")
