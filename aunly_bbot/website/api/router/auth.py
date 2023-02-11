import asyncio
import secrets

from loguru import logger
from typing import Optional
from datetime import timezone
from jose import JWTError, jwt
from graia.ariadne.app import Ariadne
from datetime import datetime, timedelta
from graia.ariadne.model import MemberPerm, Group
from graia.ariadne.exception import UnknownTarget
from fastapi.security import OAuth2PasswordBearer
from graia.amnesia.builtins.memcache import Memcache
from fastapi import APIRouter, Depends, HTTPException, status

from ....core.control import Permission
from ....core.data import get_sub_by_group
from ....core.group_config import GroupPermission
from ....model.fastapi import AuthResponse, Token, KeyResponse, InfoResponse, Info, GroupItem

SECRET_KEY = secrets.token_hex(64)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAY = 7

router = APIRouter(tags=["Auth"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/verify_key")
logger.info(f"已生成 API 密钥: {SECRET_KEY[:8]}{'*' * 20}{SECRET_KEY[-8:]}")


class UnauthorizedException(HTTPException):
    def __init__(self, detail: str = "Unauthorized"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


def create_access_token(self):
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAY)
    to_encode = {"exp": expire, "sub": self}
    return jwt.encode(
        to_encode, SECRET_KEY, algorithm=ALGORITHM, headers={"typ": "JWT", "alg": ALGORITHM}
    )


def decode_token(token: str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
    qq = payload.get("sub", "")
    return Info(
        qq=qq,
        permission=Permission.get(qq),
        token=Token(access_token=token, expires_at=payload.get("exp")),
    )


async def verify_token(token: str = Depends(oauth2_scheme)):
    try:
        return decode_token(token)
    except JWTError as e:
        raise UnauthorizedException(detail="Invalid token") from e


async def get_user_groups(qq: Optional[int] = None, master: bool = False) -> list[GroupItem]:
    app = Ariadne.current()

    async def get_group(group: Group):
        try:
            if (await app.get_member(group.id, qq or 0)).permission in [
                MemberPerm.Administrator,
                MemberPerm.Owner,
            ]:
                return group
        except UnknownTarget:
            return

    async def get_group_item(group: Group):
        return GroupItem(
            id=group.id,
            name=group.name,
            member_count=len(await app.get_member_list(group)),
            follow_count=len(get_sub_by_group(group.id)),
            is_vip=GroupPermission(group).is_vip(),
        )

    group_list = await app.get_group_list()

    return await asyncio.gather(
        *[
            get_group_item(x)
            for x in (
                group_list
                if master
                else [
                    i
                    for i in await asyncio.gather(*[get_group(group) for group in group_list])
                    if i
                ]
            )
        ]
    )


async def can_manage_groups(info: Info):
    if info.permission < Permission.MASTER:
        return await get_user_groups(int(info.qq))
    return await get_user_groups(master=True)


async def can_manage_group(info: Info, group: int):
    if info.permission > Permission.MASTER:
        return True
    app = Ariadne.current()
    try:
        can = (await app.get_member(group, int(info.qq) or 0)).permission in [
            MemberPerm.Administrator,
            MemberPerm.Owner,
        ]
    except UnknownTarget:
        can = False
    return can


@router.get("/get_key", response_model=KeyResponse, summary="获取 key")
async def get_key():
    app = Ariadne.current()
    memcache = app.launch_manager.get_interface(Memcache)
    key = secrets.token_urlsafe(16)
    await memcache.set(key, False, timedelta(seconds=120))
    return KeyResponse(data=key)


@router.get("/verify_key", response_model=AuthResponse, summary="验证 key")
async def verify_key(key: str):
    app = Ariadne.current()
    memcache = app.launch_manager.get_interface(Memcache)
    if await memcache.has(key):
        if qq := await memcache.get(key):
            await memcache.delete(key)
            return AuthResponse(
                code=status.HTTP_200_OK,
                message="",
                data=await verify_token(create_access_token(qq)),
            )
        else:
            return AuthResponse(
                code=status.HTTP_102_PROCESSING, message="Waiting for verification", data=None
            )
    else:
        return AuthResponse(code=status.HTTP_404_NOT_FOUND, message="Key not found", data=None)


@router.get("/whoami", response_model=InfoResponse, summary="获取 token 信息")
async def whoami(info: Info = Depends(verify_token)):
    return InfoResponse(data=info)
