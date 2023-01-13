import json
from pathlib import Path

subgroup_config_file = Path("data/subgroup_list.json")

subgroups = []
group_names = []

if subgroup_config_file.exists():
    data = json.loads(subgroup_config_file.read_text())
    for group_name, subgroup in data["sublist"].items():
        group_names.append(group_name)
        subgroups.append(subgroup)
else:
    subgroup_config_file.write_text(json.dumps({"sublist": {}}, ensure_ascii=False))


def get_subgroup_list() -> tuple[list, list]:
    """
    用于返回订阅组名称列表与订阅列表
    """
    return group_names, subgroups


def write_to_json():
    """
    将订阅组列表与订阅列表一一对应组装放入json文件
    """
    subgroup_config_file.write_text(
        json.dumps({"sublist": dict(zip(group_names, subgroups))}, ensure_ascii=False)
    )


class SubGroup:
    group_name: str

    def __init__(self, in_group_name: str):
        """
        init
        """
        self.group_name = in_group_name

    def is_in_group_names(self) -> bool:
        """
        判断该订阅组名称是否在订阅组列表中
        """
        return self.group_name in group_names

    def add_to_group_names(self) -> bool:
        """
        将订阅组名称添加到订阅组列表中
        """
        if self.is_in_group_names():
            return False

        group_names.append(self.group_name)
        subgroups.append([])

        write_to_json()

        return True

    def remove_from_group_names(self) -> bool:
        """
        从订阅组列表中移除该订阅组名称
        """
        if not self.is_in_group_names():
            return False
        idx = group_names.index(self.group_name)  # 获取对应的索引
        group_names.remove(self.group_name)

        subgroups.pop(idx)  # 根据索引移除列表

        write_to_json()

        return True

    def add_to_subGroups(self, up_list: list) -> bool:
        """
        将获取到的up主列表添加到对应的订阅组中
        """
        idx = group_names.index(self.group_name)  # 获取对应的索引
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
        idx = group_names.index(self.group_name)  # 获取对应的索引
        uplist: list = subgroups[idx]  # 获取对应索引的订阅列表

        if not uplist:  # 如果为空则不需要移除
            return False

        if up_id in uplist:
            uplist.remove(up_id)

        write_to_json()

        return True
