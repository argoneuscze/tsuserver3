# tsuserver3, an Attorney Online server
#
# Copyright (C) 2018 argoneus <argoneuscze@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
These decorators serve to avoid code repetition in common OOC command checks.

Note the order of the decorators matters, typically the message to be sent
to be user will be the outermost failing decorator.
"""

import functools

from server.ooc_commands.argument_types import Flag
from server.util.exceptions import ClientError, ArgumentError, AreaError


def mod_only(f):
    """ Command requires you to be logged in as a moderator. """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        client = args[0]
        if not client.get_attr("is_moderator"):
            raise ClientError("You must be logged in as a moderator to do that.")
        return f(*args, **kwargs)

    return wrapper


def casing_area_only(f):
    """ Command can only be used in a casing area. """

    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        client = args[0]
        if not client.area.get_attr("is_casing"):
            raise AreaError("This area is not intended for casing.")
        return f(*args, **kwargs)

    return wrapper


def arguments(**arg_kwargs):
    def parse_argument(string, arg_type, multiword):
        rest = ""
        if multiword:
            arg = string
        else:
            spl = string.split(maxsplit=1)
            arg = spl[0]
            if len(spl) == 2:
                rest = spl[1]

        # TODO parse arg according to arg_type
        return arg, rest

    def arguments_func(f):
        @functools.wraps(f)
        def wrapper(client, cmd_arg):
            parsed_args = dict()

            rest_cmd_arg = cmd_arg
            for name, value in arg_kwargs.items():
                optional = False
                multiword = False
                if isinstance(value, (list, tuple)):
                    arg_type, flags = value
                    optional = Flag.Optional in flags
                    multiword = Flag.Multiword in flags
                else:
                    arg_type = value

                if not rest_cmd_arg:
                    if not optional:
                        raise ArgumentError("Not enough arguments.")
                    else:
                        parsed_args[name] = ""
                        continue

                try:
                    arg_val, rest_cmd_arg = parse_argument(
                        rest_cmd_arg, arg_type, multiword
                    )
                    parsed_args[name] = arg_val
                except ArgumentError:
                    raise

            if rest_cmd_arg:
                raise ArgumentError("Too many arguments.")

            return f(client, **parsed_args)

        return wrapper

    return arguments_func
