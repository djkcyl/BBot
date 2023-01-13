# coding=utf-8
"""
Xenon 管理 https://github.com/McZoo/Xenon/blob/master/lib/control.py
"""

import time

from asyncio import Lock
from typing import Optional
from collections import defaultdict
from typing import DefaultDict, Set, Tuple, Union
from graia.broadcast.exceptions import ExecutionStop
from graia.ariadne.event.message import GroupMessage
from graia.broadcast.builtin.decorators import Depend
from graia.ariadne.model import Member, MemberPerm, Friend

from .bot_config import BotConfig


class Permission:
    """
    用于管理权限的类，不应被实例化
    """

    MASTER = 30
    GROUP_ADMIN = 20
    USER = 10
    BANNED = 0
    DEFAULT = USER

    @classmethod
    def get(cls, member: Union[Member, int, str]) -> int:
        """
        获取用户的权限

        :param member: 用户实例或QQ号
        :return: 等级，整数
        """

        if isinstance(member, Member):
            user = member.id
            user_permission = member.permission
        elif isinstance(member, (int, str)):
            user = int(member)
            user_permission = None
        else:
            raise TypeError("member must be Member or int")

        if user == 80000000:  # 该号码为匿名 QQ 号
            raise ExecutionStop()

        if user in BotConfig.admins:
            return cls.MASTER
        elif user in []:
            return cls.BANNED
        elif user_permission in [MemberPerm.Administrator, MemberPerm.Owner]:
            return cls.GROUP_ADMIN
        else:
            return cls.DEFAULT

    @classmethod
    def require(cls, level: int = DEFAULT) -> Depend:
        """
        指示需要 `level` 以上等级才能触发，默认为至少 USER 权限

        :param level: 限制等级
        """

        def perm_check(member: Member):
            member_level = cls.get(member)

            if BotConfig.Debug.enable and member.group.id not in BotConfig.Debug.groups:
                raise ExecutionStop()
            if member_level >= level:
                return
            raise ExecutionStop()

        return Depend(perm_check)

    @classmethod
    def manual(cls, member: Union[Member, Friend], level: int = DEFAULT):
        member_level = cls.get(member.id)
        if (
            isinstance(member, Member)
            and BotConfig.Debug.enable
            and member.group.id not in BotConfig.Debug.groups
        ):
            raise ExecutionStop()
        if member_level >= level:
            return
        raise ExecutionStop()


class Interval:
    """
    用于冷却管理的类，不应被实例化
    """

    last_exec: DefaultDict[int, Tuple[int, float]] = defaultdict(lambda: (1, 0.0))
    sent_alert: Set[int] = set()
    lock: Optional[Lock] = None

    @classmethod
    async def get_lock(cls):
        if not cls.lock:
            cls.lock = Lock()
        return cls.lock

    @classmethod
    def require(
        cls,
        suspend_time: float = 10,
        max_exec: int = 1,
        override_level: int = Permission.MASTER,
    ):
        """
        指示用户每执行 `max_exec` 次后需要至少相隔 `suspend_time` 秒才能再次触发功能

        等级在 `override_level` 以上的可以无视限制

        :param suspend_time: 冷却时间
        :param max_exec: 在再次冷却前可使用次数
        :param override_level: 可超越限制的最小等级
        """

        async def cd_check(event: GroupMessage):
            if Permission.get(event.sender) >= override_level:
                return
            current = time.time()
            async with (await cls.get_lock()):
                last = cls.last_exec[event.sender.id]
                if current - cls.last_exec[event.sender.id][1] >= suspend_time:
                    cls.last_exec[event.sender.id] = (1, current)
                    if event.sender.id in cls.sent_alert:
                        cls.sent_alert.remove(event.sender.id)
                    return
                elif last[0] < max_exec:
                    cls.last_exec[event.sender.id] = (last[0] + 1, current)
                    if event.sender.id in cls.sent_alert:
                        cls.sent_alert.remove(event.sender.id)
                    return
                if event.sender.id not in cls.sent_alert:
                    cls.sent_alert.add(event.sender.id)
                raise ExecutionStop()

        return Depend(cd_check)

    @classmethod
    async def manual(
        cls,
        member: Union[Member, int],
        suspend_time: float = 10,
        max_exec: int = 1,
        override_level: int = Permission.MASTER,
    ):
        if isinstance(member, Member):
            member = member.id
        if Permission.get(member) >= override_level:
            return
        current = time.time()
        async with (await cls.get_lock()):
            last = cls.last_exec[member]
            if current - cls.last_exec[member][1] >= suspend_time:
                cls.last_exec[member] = (1, current)
                if member in cls.sent_alert:
                    cls.sent_alert.remove(member)
                return
            elif last[0] < max_exec:
                cls.last_exec[member] = (last[0] + 1, current)
                if member in cls.sent_alert:
                    cls.sent_alert.remove(member)
                return
            if member not in cls.sent_alert:
                cls.sent_alert.add(member)
            raise ExecutionStop()
