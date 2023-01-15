from graia.ariadne.app import Ariadne
from fastapi import APIRouter, Depends, status
from graia.ariadne.message.chain import MessageChain

from .auth import verify_token, can_manage_group
from ....core.data import get_sub_by_group, uid_in_group
from ....utils.up_operation import subscribe_uid, unsubscribe_uid
from ....model.fastapi import Info, FollowListResponse, FollowItem, AddFollowResponse


router = APIRouter(tags=["Follow"])


@router.get("/group_follow/{group}", summary="获取群关注列表")
async def get_group_follows(group: int, info: Info = Depends(verify_token)):
    return (
        FollowListResponse(
            data=[
                FollowItem(
                    uid=str(x.uid),
                    uname=str(x.uname),
                    nick=str(x.nick or ""),
                    atall=bool(x.atall),
                    live=bool(x.live),
                    dynamic=bool(x.dynamic),
                )
                for x in get_sub_by_group(group)
            ]
        )
        if await can_manage_group(info, group)
        else FollowListResponse(
            code=status.HTTP_403_FORBIDDEN, message="Permission denied", data=[]
        )
    )


@router.put("/group_follow/{group}", summary="关注 UP")
async def add_group_follow(
    group: int, uid: str, uname: str, info: Info = Depends(verify_token)
):
    if not await can_manage_group(info, group):
        return AddFollowResponse(code=status.HTTP_403_FORBIDDEN, message="Permission denied")
    if uid_in_group(uid, group):
        return AddFollowResponse(code=6400, message=f"本群已订阅 UP {uname}（{uid}），请勿重复订阅")
    sub = await subscribe_uid(uid, group)
    if not uid_in_group(uid, group):
        return AddFollowResponse(code=6400, message=sub)
    app = Ariadne.current()
    await app.send_group_message(group, MessageChain(f"管理员已通过 Web 关注 UP {uname}（{uid}）"))
    return AddFollowResponse(message=sub)


@router.delete("/group_follow/{group}", summary="取消关注 UP")
async def del_group_follow(
    group: int, uid: str, uname: str, info: Info = Depends(verify_token)
):
    if not await can_manage_group(info, group):
        return AddFollowResponse(code=status.HTTP_403_FORBIDDEN, message="Permission denied")
    if not uid_in_group(uid, group):
        return AddFollowResponse(code=6400, message=f"本群未订阅该 UP {uname}（{uid}）")
    unsub = await unsubscribe_uid(uid, group)
    if uid_in_group(uid, group):
        return AddFollowResponse(code=6400, message=unsub)
    app = Ariadne.current()
    await app.send_group_message(group, MessageChain(f"管理员已通过 Web 取消关注 UP {uname}（{uid}）"))
    return AddFollowResponse(message=unsub)
