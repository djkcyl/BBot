from enum import Flag, auto
from typing import Optional
from bilireq.auth import Auth


class Status(Flag):
    STARTED = auto()
    """程序启动"""
    INITIALIZED = auto()
    """已初始化"""
    PUSH_IDLE = auto()
    """推送进程空闲"""
    SUBSCRIBE_IDLE = auto()
    """订阅处理进程空闲"""
    DYNAMIC_IDLE = auto()
    """动态更新进程空闲"""
    LIVE_IDLE = auto()
    """直播更新进程空闲"""
    ACCOUNT_CONNECTED = auto()
    """账号已连接"""

    ALL_STATUS = (
        STARTED
        | INITIALIZED
        | PUSH_IDLE
        | SUBSCRIBE_IDLE
        | DYNAMIC_IDLE
        | LIVE_IDLE
        | ACCOUNT_CONNECTED
    )


class BBotStatus:
    def __init__(self):
        self.status = Status(0)
        self.living: dict[str, int] = {}
        self.offset: dict[str, int] = {}
        self.last_update: Optional[str] = None
        self.last_finish: Optional[str] = None

        self.set_status(Status.DYNAMIC_IDLE, True)
        self.set_status(Status.LIVE_IDLE, True)
        self.set_status(Status.PUSH_IDLE, True)
        self.set_status(Status.SUBSCRIBE_IDLE, True)

    def set_status(self, status, value: bool):
        if value:
            self.status |= status
        else:
            self.status &= ~status

    def check_status(self, status) -> bool:
        return self.status & status == status

    def is_all_statuses_true(self, *statuses):
        all_status = Status(0)
        for status in statuses:
            all_status |= status
        return self.check_status(all_status)

    def is_all_status_true(self):
        return self.check_status(Status.ALL_STATUS)

    def to_dict(self):
        status_dict = {
            member.name: self.check_status(member) for member in Status.__members__.values()
        }
        return {
            "status": status_dict,
            "living": self.living,
            "offset": self.offset,
        }


BOT_Status = BBotStatus()
Bili_Auth = Auth()
cache = {}
