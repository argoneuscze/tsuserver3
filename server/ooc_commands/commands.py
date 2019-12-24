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
from server.util.exceptions import ClientError, AreaError, ArgumentError


@arguments(password=Type.String)
def ooc_cmd_login(client, password):
    try:
        client.auth_mod(password)
    except ClientError:
        raise
    client.send_host_message("Logged in as a moderator.")
    logger.log_server("Logged in as moderator.", client)


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
        f"[{client.area.id}][{client.get_char_name()}]Changed background to {background}",
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


@arguments(id=(Type.Integer, [Flag.Optional]))
def ooc_cmd_getarea(client, id):
    if not id:
        try:
            client.send_area_info(client.area.id)
        except AreaError:
            raise
    else:
        try:
            client.send_area_info(id)
        except AreaError:
            raise


@arguments(arg=(Type.String, [Flag.Multiword]))
def ooc_cmd_pm(client, arg):
    spl = arg.split(":", maxsplit=1)
    if len(spl) != 2:
        raise ArgumentError("Bad format. Syntax: /pm target: message")
    spl = [x.strip() for x in spl]
    target, msg = spl

    target_clients = client.server.client_manager.get_targets(client, target)
    if not target_clients:
        client.send_host_message("No targets found.")
    else:
        client.send_host_message(f"PM sent to {len(target_clients)} users: {msg}")
        for c in target_clients:
            c.send_host_message(
                "PM received from {} ({}) in {}: {}".format(
                    client.get_attr("ooc.name"),
                    client.get_char_name(),
                    client.area.get_attr("name"),
                    msg,
                )
            )
        logger.log_server(
            "[{}][{}]Sent PM to {}: {}".format(
                client.area.id, client.get_char_name(), target, msg
            ),
            client,
        )
