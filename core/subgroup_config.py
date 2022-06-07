import json
from pathlib import Path
from typing import Union

subgroup_config_file = Path("data/subgroup_list.json")

if subgroup_config_file.exists():
    data = json.loads(subgroup_config_file.read_text(encoding="utf-8"))
    groupNames = []
    subgroups = []
    for groupName, subgroup in data["sublist"].items():
        groupNames.append(groupName)
        subgroups.append(subgroup)
else:
    groupNames = []
    subgroups = []
    subgroup_config_file.write_text(
        json.dumps({"sublist": {}}), encoding="utf-8"
    )


def write_to_json():
    subgroup_config_file.write_text(
        json.dumps({"sublist": dict(zip(groupNames, subgroups))}, ensure_ascii=False)
    )


class SubGroupPermission:
    groupName: str

    def __init__(self, groupName: str):
        self.groupName = groupName

    def is_in_groupNames(self) -> bool:
        return self.groupName in groupNames

    def add_to_groupNames(self) -> bool:
        if self.is_in_groupNames():
            return False

        groupNames.append(self.groupName)
        subgroups.append([])

        write_to_json()

        return True

    def remove_from_groupNames(self) -> bool:
        if not self.is_in_groupNames():
            return False
        idx = groupNames.index(self.groupName)
        groupNames.remove(self.groupName)

        subgroups.pop(idx)

        write_to_json()

        return True

    def add_to_subGroups(self, ups: Union[list, int]) -> bool:
        if not self.is_in_groupNames():
            return False

        idx = groupNames.index(self.groupName)
        uplist = subgroups[idx]

        if type(ups) == list:
            for up in uplist:
                if up in ups:
                    ups.remove(up)
            uplist = uplist + ups
            if len(uplist) > 12:
                return False
        else:
            if ups in uplist or len(uplist) >= 12:
                return False
            uplist.append(ups)

        subgroups[idx] = uplist

        write_to_json()

        return True

    def remove_from_subGroup_ups(self, up_id: int) -> bool:
        if not self.is_in_groupNames():
            return False

        idx = groupNames.index(self.groupName)
        uplist = subgroups[idx]

        if up_id in uplist:
            uplist.remove(up_id)

        subgroups[idx] = uplist

        write_to_json()

        return True
