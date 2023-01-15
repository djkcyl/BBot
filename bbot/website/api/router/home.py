from datetime import datetime, timedelta
from graia.ariadne.app import Ariadne
from fastapi import APIRouter, Depends, HTTPException, status

from .auth import verify_token
from ....core.control import Permission
from ....core.data import get_all_uid, get_push_count, get_talk_count
from ....model.fastapi import Info, HomeResponse, TalkCount, HomeItem



router = APIRouter(tags=["Home"])


@router.get("/all", summary="获取服务器基本信息", response_model=HomeResponse)
async def home(info: Info = Depends(verify_token)):
    if info.permission < Permission.MASTER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    app = Ariadne.current()
    return HomeResponse(
        code=0,
        message="success",
        data=HomeItem(
            group_count=len(await app.get_group_list()),
            friend_count=len(await app.get_friend_list()),
            uid_count=len(get_all_uid()),
            talk_count=[
                TalkCount(time=x["time"], count=x["count"])
                for x in get_talk_count(
                    datetime.now().replace(minute=0, second=0, microsecond=0)
                    - timedelta(days=1),
                    datetime.now().replace(minute=0, second=0, microsecond=0)
                    + timedelta(hours=1),
                )
            ],
            push_count=get_push_count(
                datetime.now().replace(hour=0, minute=0, second=0, microsecond=0),
                datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
                + timedelta(days=1),
            ),
            all_push_count=get_push_count(),
        ),
    )
