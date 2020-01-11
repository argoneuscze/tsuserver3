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
from enum import Enum

from server.network.network_interface import NetworkInterface
from server.ooc_commands import commands
from server.util import logger
from server.util.exceptions import ClientError, AreaError, ArgumentError, ServerError


class AOProtocol(asyncio.Protocol):
    """
    The main class that deals with the AO protocol.
    """

    class ArgType(Enum):
        STR = (1,)
        STR_OR_EMPTY = (2,)
        INT = (3,)
        BOOL = 4

    def __init__(self, server):
        super().__init__()
        self.server = server
        self.client = None
        self.buffer = ""
        self.ping_timeout = None

    def data_received(self, data):
        """ Handles any data received from the network.

        Receives data, parses them into a command and passes it
        to the command handler.

        :param data: bytes of data
        """
        # try to decode as utf-8, ignore any erroneous characters
        self.buffer += data.decode("utf-8", "ignore")
        if len(self.buffer) > 8192:
            self.client.disconnect()
        for msg in self.get_messages():
            if len(msg) < 2:
                self.client.disconnect()
                return
            try:
                if self.server.config["debug"]:
                    print(logger.log_debug(f"[RCV]{msg}", self.client))

                cmd, *args = msg.split("#")
                self.net_cmd_dispatcher[cmd](self, args)
            except KeyError:
                return

    def connection_made(self, transport):
        """ Called upon a new client connecting

        :param transport: the transport object
        """
        self.client = self.server.new_client(NetworkInterface(transport))
        self.ping_timeout = asyncio.get_event_loop().call_later(
            self.server.config["timeout"], self.client.disconnect
        )

        # hopefully this will be deleted one day
        self.client.send_command("decryptor", "NOENCRYPT")

    def connection_lost(self, exc):
        """ User disconnected

        :param exc: reason
        """
        self.server.remove_client(self.client)
        self.ping_timeout.cancel()

    def get_messages(self):
        """ Parses out full messages from the buffer.

        :return: yields messages
        """
        while "#%" in self.buffer:
            spl = self.buffer.split("#%", 1)
            self.buffer = spl[1]
            yield spl[0]
        # exception because bad netcode
        askchar2 = "#615810BC07D12A5A#"
        if self.buffer == askchar2:
            self.buffer = ""
            yield askchar2

    def validate_net_cmd(self, args, *types, needs_auth=True):
        """ Makes sure the net command's arguments match expectations.

        :param args: actual arguments to the net command
        :param types: what kind of data types are expected
        :param needs_auth: whether you need to have chosen a character
        :return: returns True if message was validated
        """
        if needs_auth and self.client.char_id == -1:
            return False
        if len(args) != len(types):
            return False
        for i, arg in enumerate(args):
            if len(arg) == 0 and types[i] != self.ArgType.STR_OR_EMPTY:
                return False
            if types[i] == self.ArgType.INT or types[i] == self.ArgType.BOOL:
                try:
                    args[i] = int(arg)
                    if types[i] == self.ArgType.BOOL:
                        if args[i] not in (0, 1):
                            return False
                except ValueError:
                    return False
        return True

    def net_cmd_hi(self, args):
        """ Handshake.

        HI#<hdid:string>#%

        :param args: a list containing all the arguments
        """
        if not self.validate_net_cmd(args, self.ArgType.STR, needs_auth=False):
            return
        self.client.hdid = args[0]
        if self.server.ban_manager.is_banned(self.client.get_ip()):
            self.client.disconnect()
            return
        version_string = ".".join(map(str, self.server.software_version))
        self.client.send_command(
            "ID", self.client.id, self.server.software, version_string
        )
        self.client.send_command(
            "PN", self.server.get_player_count() - 1, self.server.config["playerlimit"]
        )

    def net_cmd_ch(self, _):
        """ Periodically checks the connection.

        CHECK#%

        """
        self.client.send_command("CHECK")
        self.ping_timeout.cancel()
        self.ping_timeout = asyncio.get_event_loop().call_later(
            self.server.config["timeout"], self.client.disconnect
        )

    def net_cmd_id(self, args):
        """ Client software and version

        ID#<software:string>#<version:string>#%

        """
        if not self.validate_net_cmd(
            args, self.ArgType.STR, self.ArgType.STR, needs_auth=False
        ):
            self.client.disconnect()

        software, version = args
        self.client.software = software

        if software == "AOClassic":
            # TODO remove this once FL gets removed
            self.client.send_command(
                "FL",
                "yellowtext",
                "customobjections",
                "flipping",
                "fastloading",
                "noencryption",
                "deskmod",
                "evidence",
                "cccc_ic_support",
                "arup",
                "casing_alerts",
                "modcall_reason",
            )
        elif software == "AO2":
            # TODO remove this once AO2 gets rid of FL
            self.client.send_command(
                "FL",
                "yellowtext",
                "customobjections",
                "flipping",
                "fastloading",
                "noencryption",
                "deskmod",
                "evidence",
                "cccc_ic_support",
                "arup",
                "casing_alerts",
                "modcall_reason",
            )

    def net_cmd_askchaa(self, _):
        """ Ask for the counts of characters/evidence/music

        askchaa#%

        """
        char_cnt = len(self.server.char_list)
        evi_cnt = 0
        music_cnt = 0
        self.client.send_command("SI", char_cnt, evi_cnt, music_cnt)

    def net_cmd_rc(self, _):
        """ Asks for the character list.

        RC#%

        """
        self.client.send_command("SC", *self.server.char_list)

    def net_cmd_rm(self, _):
        """ Asks for the music list.

        RM#%

        """
        self.client.send_command("SM", *self.server.music_list_network)

    def net_cmd_rd(self, _):
        """ Client is ready.

        RD#%

        """
        self.client.send_done()
        self.server.send_arup_all()
        self.client.send_motd()

    def net_cmd_cc(self, args):
        """ Character selection.

        CC#<client_id:int>#<char_id:int>#<hdid:string>#%

        """
        if not self.validate_net_cmd(
            args, self.ArgType.INT, self.ArgType.INT, self.ArgType.STR, needs_auth=False
        ):
            return
        cid = args[1]
        try:
            self.client.change_character(cid)
        except ClientError:
            return

    def net_cmd_ms(self, args):
        """ IC message.

        Refer to the implementation for details.

        """
        if self.client.get_attr(
            "ic.muted"
        ):  # Checks to see if the client has been muted by a mod
            self.client.send_host_message("You have been muted by a moderator")
            return
        if not self.client.area.can_send_message():
            return
        if not self.validate_net_cmd(
            args,
            self.ArgType.STR,  # msg_type
            self.ArgType.STR_OR_EMPTY,  # pre
            self.ArgType.STR,  # folder
            self.ArgType.STR,  # anim
            self.ArgType.STR,  # text
            self.ArgType.STR,  # pos
            self.ArgType.STR,  # sfx
            self.ArgType.INT,  # anim_type
            self.ArgType.INT,  # char_id
            self.ArgType.INT,  # sfx_delay
            self.ArgType.STR,  # button
            self.ArgType.INT,  # evidence
            self.ArgType.BOOL,  # flip
            self.ArgType.BOOL,  # ding
            self.ArgType.INT,  # color
            self.ArgType.STR_OR_EMPTY,  # showname
            self.ArgType.INT,  # charid_pair
            self.ArgType.INT,  # offset_pair
            self.ArgType.BOOL,  # nonint_pre
            self.ArgType.BOOL,  # looping SFX
            self.ArgType.BOOL,  # screenshake
            self.ArgType.STR,  # screenshake frame
            self.ArgType.STR,  # realization frame
            self.ArgType.STR,  # sfx frame
        ):
            return
        (
            msg_type,
            pre,
            folder,
            anim,
            text,
            pos,
            sfx,
            anim_type,
            cid,
            sfx_delay,
            button,
            evidence,
            flip,
            ding,
            color,
            showname,
            charid_pair,
            offset_pair,
            nonint_pre,
            loop_sfx,
            screenshake,
            frame_screenshake,
            frame_realization,
            frame_sfx,
        ) = args

        if msg_type not in ("chat", "0", "1"):
            return
        if anim_type not in (0, 1, 2, 5, 6):
            return
        if cid != self.client.char_id:
            return
        if sfx_delay < 0:
            return
        if evidence < 0:
            return
        if flip not in (0, 1):
            return
        if ding not in (0, 1):
            return
        if color not in (0, 1, 2, 3, 4, 5, 6, 7, 8):
            return
        if color == 2 and not self.client.get_attr("is_moderator"):
            color = 0

        if cur_pos := self.client.get_attr("ic.position"):
            pos = cur_pos
        else:
            try:
                self.client.change_position(pos)
            except ClientError:
                return

        button = int(button)
        if button not in (0, 1, 2, 3, 4):
            return

        showname = showname[:15]

        msg = text[:256]

        if not self.client.area.evidence_manager.is_valid_evidence(evidence):
            return

        self.client.set_attr("ic.pairing.target_char_id", charid_pair)
        self.client.set_attr("ic.pairing.offset", offset_pair)
        if anim_type not in (5, 6):
            self.client.set_attr("ic.last_emote", anim)
        self.client.set_attr("ic.flipped", flip)
        self.client.set_attr("ic.folder", folder)

        # Pairing
        other_offset = 0
        other_emote = ""
        other_flip = 0
        other_folder = ""

        paired = False
        if charid_pair > -1:
            for tgt in self.client.area.clients:
                if (
                    tgt.char_id == self.client.get_attr("ic.pairing.target_char_id")
                    and tgt.get_attr("ic.pairing.target_char_id") == self.client.char_id
                    and tgt != self.client
                    and tgt.get_attr("ic.position") == pos
                ):
                    paired = True
                    other_offset = tgt.get_attr("ic.pairing.offset")
                    other_emote = tgt.get_attr("ic.last_emote")
                    other_flip = tgt.get_attr("ic.flipped")
                    other_folder = tgt.get_attr("ic.folder")
                    break
        if not paired:
            charid_pair = -1
            offset_pair = 0

        self.client.area.send_command(
            "MS",
            msg_type,
            pre,
            folder,
            anim,
            msg,
            pos,
            sfx,
            anim_type,
            cid,
            sfx_delay,
            button,
            evidence,
            flip,
            ding,
            color,
            showname,
            charid_pair,
            other_folder,
            other_emote,
            offset_pair,
            other_offset,
            other_flip,
            nonint_pre,
            loop_sfx,
            screenshake,
            frame_screenshake,
            frame_realization,
            frame_sfx,
        )
        self.client.area.set_next_msg_delay(len(msg))
        logger.log_server(
            "[IC][{}][{}]{}".format(
                self.client.area.id, self.client.get_char_name(), msg
            ),
            self.client,
        )

    def net_cmd_ct(self, args):
        """ OOC Message

        CT#<name:string>#<message:string>#%

        """
        if not self.validate_net_cmd(args, self.ArgType.STR, self.ArgType.STR):
            return
        ooc_name = args[0]
        if self.client.get_attr("ooc.name") != ooc_name:
            self.client.set_attr("ooc.name", ooc_name)
        if ooc_name.startswith(self.server.config["hostname"]) or ooc_name.startswith(
            "<dollar>G"
        ):
            self.client.send_host_message("That name is reserved!")
            return
        if args[1].startswith("/"):
            spl = args[1][1:].split(" ", 1)
            cmd = spl[0]
            arg = ""
            if len(spl) == 2:
                arg = spl[1][:256]
            try:
                getattr(commands, "ooc_cmd_{}".format(cmd))(self.client, arg)
            except AttributeError:
                self.client.send_host_message("Invalid command.")
            except (ClientError, AreaError, ArgumentError, ServerError) as ex:
                self.client.send_host_message(ex)
        else:
            self.client.area.send_command("CT", ooc_name, args[1])
            logger.log_server(
                "[OOC][{}][{}][{}]{}".format(
                    self.client.area.id, self.client.get_char_name(), ooc_name, args[1],
                ),
                self.client,
            )

    def net_cmd_mc(self, args):
        """ Play music.

        MC#<song_name:int>#<???:int>#%

        """
        if not self.validate_net_cmd(args, self.ArgType.STR, self.ArgType.INT):
            if not self.validate_net_cmd(
                args, self.ArgType.STR, self.ArgType.INT, self.ArgType.STR
            ):
                return
        if args[1] != self.client.char_id:
            return
        try:
            area = self.server.area_manager.get_area_by_name(args[0])
            self.client.change_area(area)
        except AreaError:
            try:
                name, length = self.server.get_song_data(args[0])
                self.client.area.play_music(name, self.client.char_id, length)
                logger.log_server(
                    "[{}][{}]Changed music to {}.".format(
                        self.client.area.id, self.client.get_char_name(), name
                    ),
                    self.client,
                )
            except ServerError:
                return
        except ClientError as ex:
            self.client.send_host_message(ex)

    def net_cmd_rt(self, args):
        """ Plays the Testimony/CE animation.

        RT#<type:string>#%

        """
        if not self.validate_net_cmd(args, self.ArgType.STR):
            return
        if args[0] not in ("testimony1", "testimony2", "notguilty", "guilty"):
            return
        self.client.area.send_command("RT", args[0])
        logger.log_server(
            "[{}]{} used a judge action".format(
                self.client.area.id, self.client.get_char_name()
            ),
            self.client,
        )

    def net_cmd_hp(self, args):
        """ Sets the penalty bar.

        HP#<type:int>#<new_value:int>#%

        """
        if not self.validate_net_cmd(args, self.ArgType.INT, self.ArgType.INT):
            return
        try:
            self.client.area.change_hp(args[0], args[1])
            logger.log_server(
                "[{}]{} changed HP ({}) to {}".format(
                    self.client.area.id, self.client.get_char_name(), args[0], args[1]
                ),
                self.client,
            )
        except AreaError:
            return

    def net_cmd_pe(self, args):
        """ Adds a piece of evidence. TODO
        PE#<name:string>#<description:string>#<image:string>#%
        """
        if not self.validate_net_cmd(
            args, self.ArgType.STR, self.ArgType.STR, self.ArgType.STR
        ):
            return
        try:
            self.client.area.evidence_manager.add_evidence(*args)
        except AreaError as e:
            self.client.send_host_message(e)
        self.client.area.send_evidence_list()

    def net_cmd_de(self, args):
        """ Deletes a piece of evidence. TODO
        DE#<id:int>#%
        """
        if not self.validate_net_cmd(args, self.ArgType.INT):
            return
        idx = int(args[0])
        self.client.area.evidence_manager.delete_evidence(idx)
        self.client.area.send_evidence_list()

    def net_cmd_ee(self, args):
        """ Edits a piece of evidence. TODO
        EE#<id:int>#<name:string>#<description:string>#<image:string>#%
        """
        if not self.validate_net_cmd(
            args,
            self.ArgType.INT,
            self.ArgType.STR,
            self.ArgType.STR,
            self.ArgType.STR,
        ):
            return
        idx = int(args[0])
        self.client.area.evidence_manager.edit_evidence(idx, *args[1:])
        self.client.area.send_evidence_list()

    def net_cmd_zz(self, args):
        """ Sent on mod call.

        """
        if not self.validate_net_cmd(args, self.ArgType.STR):
            return

        msg = args[0][:80]

        self.client.send_host_message("Moderator called.")
        self.server.send_all_cmd_pred(
            "ZZ",
            "{} ({}) in {} ({}): {}".format(
                self.client.get_char_name(),
                self.client.get_ip(),
                self.client.area.name,
                self.client.area.id,
                msg,
            ),
            pred=lambda c: c.get_attr("is_moderator"),
        )
        logger.log_server(
            "[{}]{} called a moderator with reason: {}.".format(
                self.client.area.id, self.client.get_char_name(), msg
            )
        )

    def net_cmd_opKICK(self, args):
        self.net_cmd_ct(["opkick", "/kick {}".format(args[0])])

    def net_cmd_opBAN(self, args):
        self.net_cmd_ct(["opban", "/ban {}".format(args[0])])

    net_cmd_dispatcher = {
        "HI": net_cmd_hi,  # handshake
        "CH": net_cmd_ch,  # keepalive
        "ID": net_cmd_id,  # client version
        "askchaa": net_cmd_askchaa,  # ask for list lengths
        "RC": net_cmd_rc,  # character list
        "RM": net_cmd_rm,  # music list
        "RD": net_cmd_rd,  # client is ready
        "CC": net_cmd_cc,  # select character
        "MS": net_cmd_ms,  # IC message
        "CT": net_cmd_ct,  # OOC message
        "MC": net_cmd_mc,  # play song
        "RT": net_cmd_rt,  # WT/CE buttons
        "HP": net_cmd_hp,  # penalties
        "PE": net_cmd_pe,  # add evidence
        "DE": net_cmd_de,  # delete evidence
        "EE": net_cmd_ee,  # edit evidence
        "ZZ": net_cmd_zz,  # call mod button
        "opKICK": net_cmd_opKICK,  # /kick with guard on
        "opBAN": net_cmd_opBAN,  # /ban with guard on
    }
