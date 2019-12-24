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
from server.areas.evidence import Evidence
from server.util.exceptions import AreaError

LIMIT = 35


class EvidenceManager:
    def __init__(self):
        self._evidence = []

    def add_evidence(self, name, description, image):
        if len(self._evidence) >= LIMIT:
            raise AreaError("There are too many pieces of evidence.")
        evidence = Evidence(name, description, image)
        self._evidence.append(evidence)

    def edit_evidence(self, idx, name, description, image):
        try:
            evi = self._evidence[idx]
        except IndexError:
            raise AreaError("Invalid evidence ID.")
        evi.name = name
        evi.description = description
        evi.image = image

    def delete_evidence(self, idx):
        try:
            del self._evidence[idx]
        except IndexError:
            raise AreaError("Invalid evidence ID.")

    def get_evidence_list(self):
        evi_items = [[x.name, x.description, x.image] for x in self._evidence]
        return evi_items

    def is_valid_evidence(self, idx):
        return 0 <= idx <= len(self._evidence)
