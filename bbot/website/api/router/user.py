from graia.ariadne.app import Ariadne
from fastapi import APIRouter, Depends, status

from .auth import verify_token, can_manage_groups, can_manage_group
from ....model.fastapi import Info, GroupListResponse, MemberListResponse, MemberItem

router = APIRouter(tags=["Users"])


@router.get("/get_groups", response_model=GroupListResponse, summary="获取当前可管理的群列表")
async def get_groups(info: Info = Depends(verify_token)):
    """获取群列表"""
    return GroupListResponse(data=await can_manage_groups(info))


@router.get("/get_group_members/{group}", response_model=MemberListResponse, summary="获取群成员列表")
async def get_group_members(group: int, info: Info = Depends(verify_token)):
    """获取群成员列表"""
    app = Ariadne.current()
    return (
        MemberListResponse(
            data=[
                MemberItem(
                    id=x.id,
                    name=x.name,
                    permission=x.permission,
                    special_title=x.special_title,
                    join_timestamp=x.join_timestamp,
                    last_speak_timestamp=x.last_speak_timestamp,
                    mute=x.mute_time or 0,
                )
                for x in await app.get_member_list(group)
            ]
        )
        if can_manage_group(info, group)
        else GroupListResponse(
            code=status.HTTP_403_FORBIDDEN, message="Permission denied", data=[]
        )
    )
