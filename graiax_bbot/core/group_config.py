import json

from pathlib import Path
from typing import Union
from graia.ariadne.model import Group

from .bot_config import BotConfig


grouplist_file = Path("data/group_list.json")


if grouplist_file.exists():
    data = json.loads(grouplist_file.read_text(encoding="utf-8"))
    whitelist = data["white"]
    vipgroup = data["vip"]
else:
    whitelist = []
    vipgroup = []
    grouplist_file.write_text(json.dumps({"white": [], "vip": []}, indent=2))


class GroupPermission:
    def __init__(self, group: Union[str, int, Group]):
        self.group_id = group.id if isinstance(group, Group) else int(group)

    def can_join(self):
        return self.group_id in whitelist if BotConfig.access_control else True

    def add_to_whitelist(self):
        if self.group_id in whitelist:
            return False
        whitelist.append(self.group_id)
        grouplist_file.write_text(json.dumps({"white": whitelist, "vip": vipgroup}, indent=2))
        return True

    def remove_from_whitelist(self):
        if self.group_id not in whitelist:
            return False
        whitelist.remove(self.group_id)
        grouplist_file.write_text(json.dumps({"white": whitelist, "vip": vipgroup}, indent=2))
        return True

    def is_vip(self):
        return self.group_id in vipgroup

    def add_to_vips(self):
        if self.group_id in vipgroup:
            return False
        vipgroup.append(self.group_id)
        grouplist_file.write_text(json.dumps({"white": whitelist, "vip": vipgroup}, indent=2))
        return True

    def remove_from_vips(self):
        if self.group_id not in vipgroup:
            return False
        vipgroup.remove(self.group_id)
        grouplist_file.write_text(json.dumps({"white": whitelist, "vip": vipgroup}, indent=2))
        return True
