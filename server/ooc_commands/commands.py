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

from server.ooc_commands.argument_types import Type, Flag
from server.ooc_commands.decorators import arguments
from server.util import logger
from server.util.exceptions import ClientError, AreaError


@arguments(background=(Type.String, [Flag.Optional]))
def ooc_cmd_bg(client, background):
    if not background:
        client.send_host_message(
            f"The current background is {client.area.get_attr('background.name')}"
        )
        return
    if not client.get_attr("is_moderator") and client.area.get_attr(
        "background.locked"
    ):
        raise AreaError("This area's background is locked.")
    try:
        client.area.change_background(background)
    except AreaError:
        raise
    client.area.send_host_message(
        "{} changed the background to {}.".format(client.get_char_name(), background)
    )
    logger.log_server(
        "[{}][{}]Changed background to {}".format(
            client.area.id, client.get_char_name(), background
        ),
        client,
    )


@arguments(position=(Type.String, [Flag.Optional]))
def ooc_cmd_pos(client, position):
    if not position:
        client.change_position()
        client.send_host_message("Position reset.")
    else:
        try:
            client.change_position(position)
        except ClientError:
            raise
        client.send_host_message("Position changed.")
