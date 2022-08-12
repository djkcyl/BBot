import grpc.aio

from loguru import logger
from grpc import RpcError

from ..bilibili_request import get_token, bilibili_client

from .bilibili.rpc.status_pb2 import Status
from .bilibili.metadata.metadata_pb2 import Metadata
from .bilibili.metadata.device.device_pb2 import Device
from .bilibili.metadata.locale.locale_pb2 import Locale
from .bilibili.metadata.network.network_pb2 import Network
from .bilibili.app.dynamic.v2.dynamic_pb2_grpc import DynamicStub
from .bilibili.app.dynamic.v2.dynamic_pb2 import (
    DynAllReq,
    DynamicType,
    DynSpaceReq,
    DynDetailsReq,
    DynMixUpListViewMoreReq,
)

server = "grpc.biliapi.net"


def make_metadata():
    buvid = bilibili_client.fakebuvid()
    return (
        (
            "x-bili-device-bin",
            Device(
                build=6550400,
                buvid=buvid,
                mobi_app="android",
                platform="android",
                device="phone",
                channel="bili",
            ).SerializeToString(),
        ),
        (
            "x-bili-local-bin",
            Locale().SerializeToString(),
        ),
        (
            "x-bili-metadata-bin",
            Metadata(
                access_key=get_token(),
                mobi_app="android",
                device="phone",
                build=6550400,
                channel="bili",
                buvid=buvid,
                platform="android",
            ).SerializeToString(),
        ),
        ("x-bili-network-bin", Network(type="WIFI").SerializeToString()),
        ("authorization", f"identify_v1 {get_token()}".encode()),
    )


async def grpc_dyn_get(uid):
    async with grpc.aio.secure_channel(server, grpc.ssl_channel_credentials()) as channel:
        stub = DynamicStub(channel)
        req = DynSpaceReq(host_uid=int(uid))
        meta = make_metadata()
        try:
            resp = await stub.DynSpace(req, metadata=meta)
        except RpcError as e:
            for key, value in e.trailing_metadata():
                if key == "grpc-status-details-bin":
                    logger.error(Status.FromString(value))
        return resp


async def grpc_dynall_get():
    async with grpc.aio.secure_channel(server, grpc.ssl_channel_credentials()) as channel:
        stub = DynamicStub(channel)
        req = DynAllReq()
        meta = make_metadata()
        try:
            resp = await stub.DynAll(req, metadata=meta)
        except RpcError as e:
            for key, value in e.trailing_metadata():
                if key == "grpc-status-details-bin":
                    logger.error(Status.FromString(value))
            return None
        exclude_list = [
            DynamicType.ad,
            DynamicType.live,
            DynamicType.live_rcmd,
            DynamicType.banner,
        ]
        dynamic_list = [
            dyn for dyn in resp.dynamic_list.list if dyn.card_type not in exclude_list
        ]
        dynamic_list.reverse()
        return dynamic_list


async def grpc_uplist_get():
    async with grpc.aio.secure_channel(server, grpc.ssl_channel_credentials()) as channel:
        stub = DynamicStub(channel)
        req = DynMixUpListViewMoreReq(sort_type=1)
        meta = make_metadata()
        try:
            resp = await stub.DynMixUpListViewMore(req, metadata=meta)
        except RpcError as e:
            for key, value in e.trailing_metadata():
                if key == "grpc-status-details-bin":
                    logger.error(Status.FromString(value))
        return resp


async def grpc_details_get(dynamic_ids):
    async with grpc.aio.secure_channel(server, grpc.ssl_channel_credentials()) as channel:
        stub = DynamicStub(channel)
        req = DynDetailsReq(dynamic_id=str(dynamic_ids))
        meta = make_metadata()
        try:
            resp = await stub.DynDetails(req, metadata=meta)
        except RpcError as e:
            for key, value in e.trailing_metadata():
                if key == "grpc-status-details-bin":
                    logger.error(Status.FromString(value))
        return resp.list
