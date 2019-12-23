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
from server.ooc_commands.decorators import arguments, casing_area_only
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
        f"{client.get_char_name()} changed the background to {background}"
    )
    logger.log_server(
        f"[{client.area_id}][{client.get_char_name()}]Changed background to {background}",
        client,
    )


@arguments(status=(Type.String, [Flag.Optional]))
@casing_area_only
def ooc_cmd_status(client, status):
    if not status:
        client.send_host_message(f"Current status: {client.area.get_attr('status')}")
    else:
        try:
            client.area.change_status(status)
            client.area.send_host_message(
                f"{client.get_char_name()} changed status to {client.area.get_attr('status')}."
            )
            logger.log_server(
                f"[{client.area.id}][{client.get_char_name()}]Changed status to {client.area.get_attr('status')}",
                client,
            )
        except AreaError:
            raise


@arguments(name=(Type.String, [Flag.Optional]))
@casing_area_only
def ooc_cmd_cm(client, name):
    if not name:
        client.send_host_message(
            f"Current area's CM: {client.area.get_attr('case.master')}"
        )
        return

    try:
        client.area.change_cm(name)
        client.area.send_host_message(
            f"CM changed to {client.area.get_attr('case.master')}"
        )
        logger.log_server(
            f"[{client.area.id}][{client.get_char_name()}]Changed CM to {client.area.get_attr('case.master')}",
            client,
        )
    except AreaError:
        raise


@arguments()
@casing_area_only
def ooc_cmd_clearcm(client):
    try:
        client.area.change_cm("None")
        client.area.send_host_message(f"CM reset.")
        logger.log_server(
            f"[{client.area.id}][{client.get_char_name()}]Changed CM to {client.area.get_attr('case.master')}",
            client,
        )
    except AreaError:
        raise


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
