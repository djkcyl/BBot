from fastapi import APIRouter, Depends, HTTPException, status

from .auth import verify_token
from ....core.control import Permission
from ....core.bot_config import BotConfig
from ....core.bot_config import _BotConfig
from ....model.fastapi import Info, ConfigResponse


router = APIRouter(tags=["Config"])


@router.get("/", summary="获取 Bot 当前配置", response_model=ConfigResponse)
async def get_config(info: Info = Depends(verify_token)):
    if info.permission < Permission.MASTER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    return ConfigResponse(code=0, message="success", data=BotConfig)


@router.post("/", summary="修改 Bot 配置", response_model=ConfigResponse)
async def edit_config(config: _BotConfig, info: Info = Depends(verify_token)):
    if info.permission < Permission.MASTER:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied")
    try:
        BotConfig.parse_obj(config)
        BotConfig.save()
        return ConfigResponse(code=0, message="success", data=BotConfig)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=_BotConfig.valueerror_parser(e)
        ) from e
