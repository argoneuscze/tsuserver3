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
import random

from server.ooc_commands.argument_types import Type, Flag
from server.ooc_commands.decorators import arguments, casing_area_only, mod_only
from server.util import logger
from server.util.exceptions import ClientError, AreaError, ArgumentError, ServerError


@arguments()
def ooc_cmd_help(client):
    client.send_host_message(
        "To view the available commands, please check the official GitHub: {}".format(
            "https://github.com/argoneuscze/tsuserver3_origin"
        )
    )


@arguments()
def ooc_cmd_dc(client):
    ip = client.get_ip()
    other_clients = client.server.client_manager.get_targets_by_ip(ip)
    for target in other_clients:
        if target != client:
            target.disconnect()
    client.send_host_message("Other clients have been disconnected.")


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


@casing_area_only
@arguments(status=(Type.String, [Flag.Optional]))
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


@casing_area_only
@arguments(url=(Type.String, [Flag.Optional]))
def ooc_cmd_doc(client, url):
    if not url:
        doc = client.area.get_attr("case.document")
        client.send_host_message("Document: {}".format(doc))
        logger.log_server(
            "[{}][{}]Requested document. Link: {}".format(
                client.area.id, client.get_char_name(), doc
            )
        )
    else:
        client.area.change_doc(url)
        client.area.send_host_message(
            "{} changed the doc link.".format(client.get_char_name())
        )
        logger.log_server(
            "[{}][{}]Changed document to: {}".format(
                client.area.id, client.get_char_name(), url
            )
        )


@casing_area_only
@arguments()
def ooc_cmd_cleardoc(client):
    client.area.change_doc()
    client.send_host_message("Document cleared.")
    logger.log_server(
        "[{}][{}]Cleared document. Old link: {}".format(
            client.area.id,
            client.get_char_name(),
            client.area.get_attr("case.document"),
        )
    )


@casing_area_only
@arguments(name=(Type.String, [Flag.Optional]))
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


@casing_area_only
@arguments()
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


@arguments(die_size=(Type.Integer, [Flag.Optional]))
def ooc_cmd_roll(client, die_size):
    roll_max = 11037
    if die_size is not None:
        if not 1 <= die_size <= roll_max:
            raise ArgumentError("Roll value must be between 1 and {}.".format(roll_max))
    else:
        die_size = 6
    roll = random.randint(1, die_size)
    client.area.send_host_message(
        "{} rolled {} out of {}.".format(client.get_char_name(), roll, die_size)
    )
    logger.log_server(
        "[{}][{}]Used /roll and got {} out of {}.".format(
            client.area.id, client.get_char_name(), roll, die_size
        )
    )


@arguments()
def ooc_cmd_coinflip(client):
    coin = ["heads", "tails"]
    flip = random.choice(coin)
    client.area.send_host_message(
        "{} flipped a coin and got {}.".format(client.get_char_name(), flip)
    )
    logger.log_server(
        "[{}][{}]Used /coinflip and got {}.".format(
            client.area.id, client.get_char_name(), flip
        )
    )


@mod_only
@arguments(arg=(Type.String, [Flag.Multiword]))
def ooc_cmd_kick(client, arg):
    targets = client.server.client_manager.get_targets(client, arg)
    if targets:
        for c in targets:
            logger.log_server("Kicked {}.".format(c.get_ip()), client)
            c.disconnect()
        client.send_host_message("Kicked {} client(s).".format(len(targets)))
    else:
        client.send_host_message("No targets found.")


@mod_only
@arguments(arg=(Type.String, [Flag.Multiword]))
def ooc_cmd_mute(client, arg):
    targets = client.server.client_manager.get_targets(client, arg)
    if targets:
        for c in targets:
            logger.log_server("Muted {}.".format(c.get_ip()), client)
            c.set_attr("ic.muted", True)
        client.send_host_message("Muted {} client(s).".format(len(targets)))
    else:
        client.send_host_message("No targets found.")


@mod_only
@arguments(arg=(Type.String, [Flag.Multiword]))
def ooc_cmd_unmute(client, arg):
    targets = client.server.client_manager.get_targets(client, arg)
    if targets:
        for c in targets:
            logger.log_server("Unmuted {}.".format(c.get_ip()), client)
            c.set_attr("ic.muted", False)
        client.send_host_message("Unmuted {} client(s).".format(len(targets)))
    else:
        client.send_host_message("No targets found.")


@mod_only
@arguments(ip=Type.String)
def ooc_cmd_banip(client, ip):
    ip = ip.strip()
    if len(ip) < 7:
        raise ArgumentError("You must specify an IP.")
    try:
        client.server.ban_manager.add_ban(ip)
    except ServerError:
        raise
    targets = client.server.client_manager.get_targets_by_ip(ip)
    if targets:
        for c in targets:
            c.disconnect()
        client.send_host_message("Kicked {} existing client(s).".format(len(targets)))
    client.send_host_message("Added {} to the banlist.".format(ip))
    logger.log_server("Banned {}.".format(ip), client)
