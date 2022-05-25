import json
from pathlib import Path
from typing import Union
from graia.ariadne.model import Group

from .bot_config import BotConfig


grouplist_file = Path("data/white_list.json")


if grouplist_file.exists():
    data = json.loads(grouplist_file.read_text(encoding="utf-8"))
    whitelist = data["white"]
else:
    whitelist = []
    grouplist_file.write_text(json.dumps({"white": []}, indent=2))


class GroupPermission:
    def __init__(self, group: Union[int, Group]):
        self.group_id = group.id if isinstance(group, Group) else int(group)

    def can_join(self):
        return self.group_id in whitelist if BotConfig.access_control else True

    def add_to_whitelist(self):
        if self.group_id in whitelist:
            return False
        whitelist.append(self.group_id)
        grouplist_file.write_text(json.dumps({"white": whitelist}, indent=2))
        return True

    def remove_from_whitelist(self):
        if self.group_id not in whitelist:
            return False
        whitelist.remove(self.group_id)
        grouplist_file.write_text(json.dumps({"white": whitelist}, indent=2))
        return True
