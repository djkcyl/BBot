import json
from pathlib import Path

subgroup_config_file = Path("data/subgroup_list.json")

groupNames = []
subgroups = []

if subgroup_config_file.exists():
    data = json.loads(subgroup_config_file.read_text())
    for groupName, subgroup in data["sublist"].items():
        groupNames.append(groupName)
        subgroups.append(subgroup)
else:
    subgroup_config_file.write_text(json.dumps({"sublist": {}}, ensure_ascii=False))


def get_subgroup_list() -> tuple[list, list]:
    """
    用于返回订阅组名称列表与订阅列表
    """
    return groupNames, subgroups


def write_to_json():
    """
    将订阅组列表与订阅列表一一对应组装放入json文件
    """
    subgroup_config_file.write_text(
        json.dumps({"sublist": dict(zip(groupNames, subgroups))}, ensure_ascii=False)
    )


class SubGroup:
    groupName: str

    def __init__(self, groupName: str):
        """
        init
        """
        self.groupName = groupName

    def is_in_groupNames(self) -> bool:
        """
        判断该订阅组名称是否在订阅组列表中
        """
        return self.groupName in groupNames

    def add_to_groupNames(self) -> bool:
        """
        将订阅组名称添加到订阅组列表中
        """
        if self.is_in_groupNames():
            return False

        groupNames.append(self.groupName)
        subgroups.append([])

        write_to_json()

        return True

    def remove_from_groupNames(self) -> bool:
        """
        从订阅组列表中移除该订阅组名称
        """
        if not self.is_in_groupNames():
            return False
        idx = groupNames.index(self.groupName)  # 获取对应的索引
        groupNames.remove(self.groupName)

        subgroups.pop(idx)  # 根据索引移除列表

        write_to_json()

        return True

    def add_to_subGroups(self, up_list: list) -> bool:
        """
        将获取到的up主列表添加到对应的订阅组中
        """
        idx = groupNames.index(self.groupName)  # 获取对应的索引
        uplist: list = subgroups[idx]  # 获取对应索引的订阅列表

        for up in uplist:  # 判断是否已经有相同的uid
            if up in up_list:
                up_list.remove(up)
        uplist += up_list
        if len(uplist) > 12:
            return False

        subgroups[idx] = uplist  # 替换订阅列表

        write_to_json()

        return True

    def remove_from_subGroup_ups(self, up_id: int) -> bool:
        """
        从对应订阅组中移除指定的up主
        """
        idx = groupNames.index(self.groupName)  # 获取对应的索引
        uplist: list = subgroups[idx]  # 获取对应索引的订阅列表

        if not uplist:  # 如果为空则不需要移除
            return False

        if up_id in uplist:
            uplist.remove(up_id)

        write_to_json()

        return True
