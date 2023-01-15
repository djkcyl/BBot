from typing import Optional
from starlette import status
from datetime import datetime
from pydantic import BaseModel
from graia.ariadne.model import MemberPerm

from ..model.config import _BotConfig


class Token(BaseModel):
    access_token: str
    expires_at: Optional[datetime] = None
    token_type: str = "bearer"


class Info(BaseModel):
    qq: str
    permission: int
    token: Token


class BaseResponse(BaseModel):
    code: int = status.HTTP_200_OK
    message: str = "Success"


class AuthResponse(BaseResponse):
    data: Optional[Info]


class KeyResponse(BaseResponse):
    data: str


class InfoResponse(BaseResponse):
    data: Info


class GroupItem(BaseModel):
    id: int
    name: str
    member_count: int
    follow_count: int
    is_vip: bool


class GroupListResponse(BaseResponse):
    data: Optional[list[GroupItem]]


class MemberItem(BaseModel):
    id: int
    name: str
    permission: MemberPerm
    special_title: Optional[str]
    join_timestamp: Optional[int]
    last_speak_timestamp: Optional[int]
    mute: Optional[int]


class MemberListResponse(BaseResponse):
    data: Optional[list[MemberItem]]


class FollowItem(BaseModel):
    uid: str
    uname: str
    nick: Optional[str]
    atall: bool
    live: bool
    dynamic: bool


class FollowListResponse(BaseResponse):
    data: Optional[list[FollowItem]]


class AddFollowResponse(BaseResponse):
    pass


class TalkCount(BaseModel):
    time: int
    count: int


class HomeItem(BaseModel):
    group_count: int
    friend_count: int
    uid_count: int
    push_count: int
    all_push_count: int
    talk_count: list[TalkCount]


class HomeResponse(BaseResponse):
    data: HomeItem


class ConfigResponse(BaseResponse):
    data: _BotConfig
