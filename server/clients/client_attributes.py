# tsuserver3, an Attorney Online server
#
# Copyright (C) 2019 argoneus <argoneuscze@gmail.com>
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


def default_attributes():
    return {
        "client": {"is_moderator": False},
        "ic": {"position": "", "muted": False},
        "ooc": {"name": None},
        "global": {"muted": False},
        "adverts": {"muted": False},
    }


def get_dict_attribute(dictionary, attr_path):
    path_split = attr_path.split(".")
    for path in path_split:
        dictionary = dictionary[path]
    return dictionary


def set_dict_attribute(dictionary, attr_path, value):
    path_split = attr_path.split(".", maxsplit=1)
    key = path_split[0]
    if len(path_split) == 1:
        dictionary[key] = value
        return
    path = path_split[1]
    set_dict_attribute(dictionary[key], path, value)
