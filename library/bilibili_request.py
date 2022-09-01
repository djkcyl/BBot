import httpx

from typing import Union
from bilireq.utils import post
from bilireq.grpc.protos.bilibili.app.dynamic.v2.dynamic_pb2_grpc import DynamicStub
from bilireq.grpc.protos.bilibili.app.dynamic.v2.dynamic_pb2 import (
    DynamicType,
    DynDetailsReq,
    DynDetailsReply,
)
from bilireq.grpc.utils import grpc_request
from bilireq.grpc.dynamic import grpc_get_followed_dynamics

from core import Bili_Auth

hc = httpx.AsyncClient()


async def relation_modify(uid: Union[str, int], act: int):
    """
    修改关系

    Args:
        uid: 用户ID
        act: 操作
    Act:
        1:	 关注
        2:	 取关
        3:	 悄悄关注
        4:	 取消悄悄关注
        5:	 拉黑
        6:	 取消拉黑
        7:	 踢出粉丝团
    """
    url = "https://api.bilibili.com/x/relation/modify"
    data = {
        "act": act,
        "fid": int(uid),
    }
    return await post(url, params=data, auth=Bili_Auth, raw=True)


async def dynamic_like(dynid):
    """
    动态点赞

    Args:
        dynid: 动态ID
    """
    url = "https://api.vc.bilibili.com/dynamic_like/v1/dynamic_like/thumb"
    data = {"dynamic_id": str(dynid), "up": 1}
    return await post(url, data=data, auth=Bili_Auth)


async def get_b23_url(burl: str) -> str:
    """
    b23 链接转换

    Args:
        burl: 需要转换的 BiliBili 链接
    """
    url = "https://api.bilibili.com/x/share/click"
    data = {
        "build": 6700300,
        "buvid": 0,
        "oid": burl,
        "platform": "android",
        "share_channel": "COPY",
        "share_id": "public.webview.0.0.pv",
        "share_mode": 3,
    }
    return (await post(url, data=data))["content"]


async def search_user(keyword: str):
    """
    搜索用户
    """
    url = "https://api.bilibili.com/x/web-interface/search/type"
    data = {"keyword": keyword, "search_type": "bili_user"}
    return (await hc.get(url, params=data)).json()["data"]


async def grpc_get_followed_dynamics_noads():
    resp = await grpc_get_followed_dynamics(auth=Bili_Auth)
    exclude_list = [
        DynamicType.ad,
        DynamicType.live,
        DynamicType.live_rcmd,
        DynamicType.banner,
    ]
    dynamic_list = [dyn for dyn in resp.dynamic_list.list if dyn.card_type not in exclude_list]
    dynamic_list.reverse()
    return dynamic_list


@grpc_request
async def grpc_get_dynamic_details(dynamic_ids: str, **kwargs) -> DynDetailsReply:
    stub = DynamicStub(kwargs.pop("_channel"))
    req = DynDetailsReq(dynamic_ids=dynamic_ids)
    return await stub.DynDetails(req, **kwargs)
